# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2018 Vifib SARL and Contributors. All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsibility of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# guarantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

import glob
import os
import textwrap
import logging
import time
import errno
import socket
import pwd

from six.moves import urllib
from six.moves import http_client

try:
  import subprocess32 as subprocess
except ImportError:
  import subprocess

try:
  from typing import TYPE_CHECKING, Optional, Iterable, Dict, Union
  if TYPE_CHECKING:
    import subprocess
except ImportError: # XXX to be removed once we depend on typing
  pass

import zope.interface
import psutil

from .interface.slap import IException
from .interface.slap import ISupply
from .interface.slap import IRequester
from ..grid.slapgrid import SLAPGRID_PROMISE_FAIL

from .slap import slap
from ..util import dumps, rmtree

from ..grid.svcbackend import getSupervisorRPC
from ..grid.svcbackend import _getSupervisordSocketPath


@zope.interface.implementer(IException)
class SlapOSNodeCommandError(Exception):
  """Exception raised when running a SlapOS Node command failed.
  """
  def __str__(self):
    # This is a false positive in pylint https://github.com/PyCQA/pylint/issues/1498
    called_process_error = self.args[0] #  pylint: disable=unsubscriptable-object
    return "{} exitstatus: {} output:\n{}".format(
        self.__class__.__name__,
        called_process_error['exitstatus'],
        called_process_error['output'],
    )


@zope.interface.implementer(IException)
class SlapOSNodeSoftwareError(SlapOSNodeCommandError):
  """Exception raised when runing SlapOS Node software command failed.
  """

@zope.interface.implementer(IException)
class SlapOSNodeInstanceError(SlapOSNodeCommandError):
  """Exception raised when runing SlapOS Node instance command failed.
  """

@zope.interface.implementer(IException)
class SlapOSNodeReportError(SlapOSNodeCommandError):
  """Exception raised when runing SlapOS Node report command failed.
  """

@zope.interface.implementer(IException)
class PathTooDeepError(Exception):
  """Exception raised when path is too deep to create an unix socket.
  """


class ConfigWriter(object):
  """Base class for an object writing a config file or wrapper script.
  """
  def __init__(self, standalone_slapos):
    self._standalone_slapos = standalone_slapos

  def writeConfig(self, path):
    NotImplemented


class SupervisorConfigWriter(ConfigWriter):
  """Write supervisor configuration at etc/supervisor.conf
  """
  def _getProgramConfig(self, program_name, command, stdout_logfile):
    """Format a supervisor program block.
    """
    return textwrap.dedent(
        """\
        [program:{program_name}]
        command = {command}
        autostart = false
        autorestart = false
        startretries = 0
        startsecs = 0
        redirect_stderr = true
        stdout_logfile = {stdout_logfile}
        stdout_logfile_maxbytes = 5MB
        stdout_logfile_backups = 0

    """).format(**locals())

  def _getSupervisorConfigParts(self):
    """Iterator on parts of formatted config.
    """
    standalone_slapos = self._standalone_slapos
    yield textwrap.dedent(
        """
        [unix_http_server]
        file = {standalone_slapos._supervisor_socket}

        [supervisorctl]
        serverurl = unix://{standalone_slapos._supervisor_socket}

        [supervisord]
        logfile = {standalone_slapos._supervisor_log}
        pidfile = {standalone_slapos._supervisor_pid}
        childlogdir = {standalone_slapos._log_directory}
        strip_ansi = true

        [rpcinterface:supervisor]
        supervisor.rpcinterface_factory = supervisor.rpcinterface:make_main_rpcinterface

        [program:slapos-proxy]
        command = {standalone_slapos._slapos_bin} proxy start --cfg {standalone_slapos._slapos_config} --verbose
        startretries = 0
        startsecs = 0
        redirect_stderr = true
        stdout_logfile = {standalone_slapos._log_directory}/slapos-proxy.log

        [program:slapos-instance-supervisord]
        command = supervisord --nodaemon --configuration {standalone_slapos._instance_root}/etc/supervisord.conf
        startretries = 0
        startsecs = 0
        redirect_stderr = true
        stdout_logfile = {standalone_slapos._log_directory}/slapos-instance-supervisord.log

        """).format(**locals())

    for program, program_config in standalone_slapos._slapos_commands.items():
      yield self._getProgramConfig(
          program,
          program_config['command'].format(
              self=standalone_slapos, debug_args=''),
          stdout_logfile=program_config['stdout_logfile'].format(self=standalone_slapos))

  def writeConfig(self, path):
    with open(path, 'w') as f:
      for part in self._getSupervisorConfigParts():
        f.write(part)


class SlapOSConfigWriter(ConfigWriter):
  """Write slapos configuration at etc/slapos.cfg
  """
  def _getPartitionForwardConfiguration(self):
    # type: () -> Iterable[str]
    for pfc in self._standalone_slapos._partition_forward_configuration:
      software_release_list = '\n  '.join(pfc.software_release_list)
      config = '[multimaster/{pfc.master_url}]\n'.format(pfc=pfc)
      if pfc.cert:
        config += 'cert = {pfc.cert}\n'.format(pfc=pfc)
      if pfc.key:
        config += 'key = {pfc.key}\n'.format(pfc=pfc)
      config += 'software_release_list =\n  {}\n'.format('\n  '.join(pfc.software_release_list))
      if isinstance(pfc, PartitionForwardAsPartitionConfiguration):
        config += "computer = {pfc.computer}\n".format(pfc=pfc)
        config += "partition = {pfc.partition}\n".format(pfc=pfc)
      yield config

  def writeConfig(self, path):
    # type: (str) -> None
    standalone_slapos = self._standalone_slapos
    read_only_shared_part_list = '\n  '.join( #  pylint: disable=unused-variable; used in format()
        standalone_slapos._shared_part_list)
    partition_forward_configuration = '\n'.join(self._getPartitionForwardConfiguration())
    with open(path, 'w') as f:
      f.write(
          textwrap.dedent(
              """
              [slapos]
              software_root = {standalone_slapos._software_root}
              instance_root = {standalone_slapos._instance_root}
              shared_part_list =
                {read_only_shared_part_list}
                {standalone_slapos._shared_part_root}
              master_url = {standalone_slapos._master_url}
              master_rest_url = {standalone_slapos._master_url}/hateoas
              computer_id = {standalone_slapos._computer_id}
              root_check = False
              pidfile_software = {standalone_slapos._instance_pid}
              pidfile_instance = {standalone_slapos._software_pid}
              pidfile_report =  {standalone_slapos._report_pid}
              forbid_supervisord_automatic_launch = true

              [slapformat]
              input_definition_file = {standalone_slapos._slapformat_definition}
              partition_amount = {standalone_slapos._partition_count}
              alter_user = false
              alter_network = false
              create_tap = false
              create_tun = false
              computer_xml = {standalone_slapos._slapos_xml}

              [slapproxy]
              host = {standalone_slapos._server_ip}
              port = {standalone_slapos._server_port}
              database_uri = {standalone_slapos._proxy_database}
              local_software_release_root = {standalone_slapos._local_software_release_root}

              {partition_forward_configuration}
              """).format(**locals()))


class SlapOSCommandWriter(ConfigWriter):
  """Write a bin/slapos wrapper.
  """
  def writeConfig(self, path):
    with open(path, 'w') as f:
      f.write(
          textwrap.dedent(
              """\
              #!/bin/sh
              SLAPOS_CONFIGURATION={self._standalone_slapos._slapos_config} \\
              SLAPOS_CLIENT_CONFIGURATION=$SLAPOS_CONFIGURATION \\
              exec {self._standalone_slapos._slapos_bin} "$@"
      """).format(**locals()))
    os.chmod(path, 0o755)


class SlapOSNodeAutoWriter(ConfigWriter):
  """Write a bin/slapos-node-auto wrapper.
  """
  def writeConfig(self, path):
    with open(path, 'w') as f:
      f.write(
          textwrap.dedent(
              """\
              #!/bin/sh
              while true
              do
                for i in $(seq 1 60)
                do
                  supervisorctl -c {self._standalone_slapos._supervisor_config} start slapos-node-software &
                  supervisorctl -c {self._standalone_slapos._supervisor_config} start slapos-node-instance &
                  sleep 60
                done
                supervisorctl -c {self._standalone_slapos._supervisor_config} start slapos-node-report &
              done
      """).format(**locals()))
    os.chmod(path, 0o755)


class SlapformatDefinitionWriter(ConfigWriter):
  """Write slapformat-definition.cfg configuration.
  """
  def writeConfig(self, path):
    ipv4 = self._standalone_slapos._ipv4_address
    ipv6 = self._standalone_slapos._ipv6_address
    ipv4_cidr = ipv4 + '/255.255.255.255' if ipv4 else ''
    ipv6_cidr = ipv6 + '/64' if ipv6 else ''
    user = pwd.getpwuid(os.getuid()).pw_name
    partition_base_name = self._standalone_slapos._partition_base_name
    with open(path, 'w') as f:
      f.write(
          textwrap.dedent(
              """
              [computer]
              address = {ipv4_cidr}\n
      """).format(**locals()))
      for i in range(self._standalone_slapos._partition_count):
        f.write(
            textwrap.dedent(
                """
                [partition_{i}]
                address = {ipv6_cidr} {ipv4_cidr}
                pathname = {partition_base_name}{i}
                user = {user}
                network_interface =\n
        """).format(**locals()))


class PartitionForwardConfiguration(object):
  """Specification of request forwarding to another master, requested as user.
  """
  def __init__(
      self,
      master_url,
      cert=None,
      key=None,
      software_release_list=(),
  ):
    # type: (str, Optional[str], Optional[str], Iterable[str]) -> None
    self.master_url = master_url
    self.cert = cert
    self.key = key
    self.software_release_list = list(software_release_list)


class PartitionForwardAsPartitionConfiguration(PartitionForwardConfiguration):
  """Specification of request forwarding to another master, requested as partition.
  """
  def __init__(
      self,
      master_url,
      computer,
      partition,
      cert=None,
      key=None,
      software_release_list=(),
  ):
    # type: (str, str, str, Optional[str], Optional[str], Iterable[str]) -> None
    super(PartitionForwardAsPartitionConfiguration, self).__init__(
        master_url,
        cert,
        key,
        software_release_list,
    )
    self.computer = computer
    self.partition = partition


@zope.interface.implementer(ISupply, IRequester)
class StandaloneSlapOS(object):
  """A SlapOS that can be embedded in other applications, also useful for testing.

  This plays the role of an `IComputer` where users of classes implementing this
  interface can install software, create partitions and access parameters of the
  running partitions.

  Extends the existing `IRequester` and `ISupply`, with the special behavior that
  `IRequester.request` and `ISupply.supply` will only use the embedded computer.
  """
  # an "hidden" flag to run slapos node instance and software with --all, for
  # test suites for softwares with missing promises.
  _force_slapos_node_instance_all = False

  def __init__(
      self,
      base_directory,
      server_ip,
      server_port,
      computer_id='local',
      shared_part_list=(),
      software_root=None,
      instance_root=None,
      shared_part_root=None,
      partition_forward_configuration=(),
      slapos_bin='slapos',
      local_software_release_root=os.sep,
    ):
    # type: (str, str, int, str, Iterable[str], Optional[str], Optional[str], Optional[str], Iterable[Union[PartitionForwardConfiguration, PartitionForwardAsPartitionConfiguration]], str, str) -> None
    """Constructor, creates a standalone slapos in `base_directory`.

    Arguments:
      * `base_directory`  -- the directory which will contain softwares and instances.
      * `server_ip`, `server_port` -- the address this SlapOS proxy will listen to.
      * `computer_id` -- the id of this computer.
      * `shared_part_list` -- list of extra paths to use as read-only ${buildout:shared-part-list}.
      * `software_root` -- directory to install software, default to "soft" in `base_directory`
      * `instance_root` -- directory to create instances, default to "inst" in `base_directory`
      * `shared_part_root` -- directory to hold shared parts software, default to "shared" in `base_directory`.
      * `partition_forward_configuration` -- configuration of partition request forwarding to external SlapOS master.
      * `slapos_bin` -- slapos executable to use, default to "slapos" (thus depending on the runtime PATH).
      * `local_software_release_root` -- root for local Software Releases paths in the SlapOS proxy, default to `/`.

    Error cases:
      * `PathTooDeepError` when `base_directory` is too deep. Because of limitation
        with the length of paths of UNIX sockets, too deep paths cannot be used.
        Note that once slapns work is integrated, this should not be an issue anymore.
    """
    self._logger = logging.getLogger(__name__)

    # slapos proxy address
    self._server_ip = server_ip
    self._server_port = server_port
    self._master_url = "http://{server_ip}:{server_port}".format(**locals())
    self._local_software_release_root = local_software_release_root

    self._base_directory = base_directory
    self._shared_part_list = list(shared_part_list)
    self._partition_forward_configuration = list(partition_forward_configuration)
    self._partition_count = 0
    self._partition_base_name = 'slappart'
    self._ipv4_address = None
    self._ipv6_address = None

    self._slapos_bin = slapos_bin

    self._slapos_commands = {
        'slapos-node-software': {
            'command':
                '{self._slapos_bin} node software --cfg {self._slapos_config} {debug_args}',
            'debug_args':
                '-v --buildout-debug',
            'stdout_logfile':
                '{self._log_directory}/slapos-node-software.log',
        },
        'slapos-node-software-all': {
            'command':
                '{self._slapos_bin} node software --cfg {self._slapos_config} --all {debug_args}',
            'debug_args':
                '-v --buildout-debug',
            'stdout_logfile':
                '{self._log_directory}/slapos-node-software.log',
        },
        'slapos-node-instance': {
            'command':
                '{self._slapos_bin} node instance --cfg {self._slapos_config} {debug_args}',
            'debug_args':
                '-v --buildout-debug',
            'stdout_logfile':
                '{self._log_directory}/slapos-node-instance.log',
        },
        'slapos-node-instance-all': {
            'command':
                '{self._slapos_bin} node instance --cfg {self._slapos_config} --all {debug_args}',
            'debug_args':
                '-v --buildout-debug',
            'stdout_logfile':
                '{self._log_directory}/slapos-node-instance.log',
        },
        'slapos-node-report': {
            'command':
                '{self._slapos_bin} node report --cfg {self._slapos_config} {debug_args}',
            'stdout_logfile':
                '{self._log_directory}/slapos-node-report.log',
        },
        'slapos-node-auto': {
            'command':
                '{self._slapos_node_auto_bin}',
            'stdout_logfile':
                '{self._log_directory}/slapos-node-auto.log',
        }
    }
    self._computer_id = computer_id
    self._slap = slap()
    self._slap.initializeConnection(self._master_url)

    self._initBaseDirectory(software_root, instance_root, shared_part_root)

  def _initBaseDirectory(self, software_root, instance_root, shared_part_root):
    """Create the directory after checking it's not too deep.
    """
    base_directory = self._base_directory
    # To prevent error: Cannot open an HTTP server: socket.error reported
    # AF_UNIX path too long This `base_directory` should not be too deep.
    # Socket path is 108 char max on linux
    # https://github.com/torvalds/linux/blob/3848ec5/net/unix/af_unix.c#L234-L238
    # Supervisord socket name contains the pid number, which is why we add
    # .xxxxxxx in this check.
    if len(os.path.join(base_directory, 'sv.sock.xxxxxxx')) > 108:
      raise PathTooDeepError(
          'working directory ( {base_directory} ) is too deep'.format(
              **locals()))

    def ensureDirectoryExists(d):
      if not os.path.exists(d):
        os.mkdir(d)

    self._software_root = software_root if software_root else os.path.join(
        base_directory, 'soft')
    self._instance_root = instance_root if instance_root else os.path.join(
        base_directory, 'inst')
    self._shared_part_root = shared_part_root if shared_part_root else os.path.join(
        base_directory, 'shared')
    for d in (self._software_root, self._instance_root, self._shared_part_root):
      ensureDirectoryExists(d)
      os.chmod(d, 0o750)

    etc_directory = os.path.join(base_directory, 'etc')
    ensureDirectoryExists(etc_directory)
    self._supervisor_config = os.path.join(etc_directory, 'supervisord.conf')
    self._slapos_config = os.path.join(etc_directory, 'slapos.cfg')
    self._slapformat_definition = os.path.join(etc_directory, 'slapformat-definition.cfg')
    self._slapos_xml = os.path.join(etc_directory, 'slapos.xml')

    var_directory = os.path.join(base_directory, 'var')
    ensureDirectoryExists(var_directory)
    self._proxy_database = os.path.join(var_directory, 'proxy.db')

    # for convenience, make a slapos command for this instance
    bin_directory = os.path.join(base_directory, 'bin')
    ensureDirectoryExists(bin_directory)

    self._slapos_wrapper = os.path.join(bin_directory, 'slapos')
    self._slapos_node_auto_bin = os.path.join(bin_directory, 'slapos-node-auto')

    self._log_directory = os.path.join(var_directory, 'log')
    ensureDirectoryExists(self._log_directory)
    self._supervisor_log = os.path.join(self._log_directory, 'supervisord.log')

    run_directory = os.path.join(var_directory, 'run')
    ensureDirectoryExists(run_directory)
    self._supervisor_pid = os.path.join(run_directory, 'supervisord.pid')
    self._software_pid = os.path.join(run_directory, 'slapos-node-software.pid')
    self._instance_pid = os.path.join(run_directory, 'slapos-node-instance.pid')
    self._report_pid = os.path.join(run_directory, 'slapos-node-report.pid')

    self._supervisor_socket = os.path.join(run_directory, 'sv.sock')

    SupervisorConfigWriter(self).writeConfig(self._supervisor_config)
    SlapOSConfigWriter(self).writeConfig(self._slapos_config)
    SlapformatDefinitionWriter(self).writeConfig(self._slapformat_definition)
    SlapOSCommandWriter(self).writeConfig(self._slapos_wrapper)
    SlapOSNodeAutoWriter(self).writeConfig(self._slapos_node_auto_bin)

    self.start()

  @property
  def computer(self):
    """Access the computer.
    """
    return self._slap.registerComputer(self._computer_id)

  @property
  def software_directory(self):
    # type: () -> str
    """Path to software directory
    """
    return self._software_root

  @property
  def shared_directory(self):
    # type: () -> str
    """Path to shared parts directory
    """
    return self._shared_part_root

  @property
  def instance_directory(self):
    # type: () -> str
    """Path to instance directory
    """
    return self._instance_root

  @property
  def system_supervisor_rpc(self):
    """A xmlrpc connection to control the "System" supervisor.

    The system supervisor is used internally by StandaloneSlapOS to start
    slap proxy and run slapos node commands.

    This should be used as a context manager.
    """
    return getSupervisorRPC(self._supervisor_socket)

  @property
  def instance_supervisor_rpc(self):
    """A xmlrpc connection to control the "Instance" supervisor.

    The instance supervisor is the one started implictly by slapos node instance.

    This should be used as a context manager.
    """
    return getSupervisorRPC(_getSupervisordSocketPath(self._instance_root, self._logger))

  def format(
      self,
      partition_count,
      ipv4_address,
      ipv6_address,
      partition_base_name="slappart"):
    """Creates `partition_count` partitions.

    All partitions have the same `ipv4_address` and `ipv6_address` and
    use the current system user.

    When calling this a second time with a lower `partition_count` or with
    different `partition_base_name` will delete existing partitions.

    Error cases:
        * ValueError when re-formatting should delete partitions that are busy.
    """
    for path in (
        self._software_root,
        self._shared_part_root,
        self._instance_root,
    ):
      if not os.path.exists(path):
        os.mkdir(path)

    # check for partitions to remove
    unknown_partition_set = set([])
    for path in glob.glob(os.path.join(self._instance_root, '*')):
      # var and etc are some slapos "system" directories, not partitions
      if os.path.isdir(path) and os.path.basename(path) not in ('var', 'etc'):
        unknown_partition_set.add(path)

    # create partitions and configure computer
    partition_list = []
    for i in range(partition_count):
      partition_reference = '%s%s' % (partition_base_name, i)

      partition_path = os.path.join(self._instance_root, partition_reference)
      unknown_partition_set.discard(partition_path)
      if not (os.path.exists(partition_path)):
        os.mkdir(partition_path)
      os.chmod(partition_path, 0o750)
      partition_list.append({
          'address_list': [
              {
                  'addr': ipv4_address,
                  'netmask': '255.255.255.255'
              },
              {
                  'addr': ipv6_address,
                  'netmask': 'ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff'
              },
          ],
          'path': partition_path,
          'reference': partition_reference,
          'tap': {
              'name': partition_reference
          },
      })

    if unknown_partition_set:
      # sanity check that we are not removing partitions in use
      computer_partition_dict = {
          computer_part.getId(): computer_part
          for computer_part in self.computer.getComputerPartitionList()
      }
      for part in unknown_partition_set:
        # used in format(**locals()) below
        part_id = os.path.basename(part)  # pylint: disable=unused-variable
        computer_partition = computer_partition_dict.get(os.path.basename(part))
        if computer_partition is not None \
             and computer_partition.getState() != "destroyed":
          raise ValueError(
              "Cannot reformat to remove busy partition at {part_id}".format(
                  **locals()))

    self.computer.updateConfiguration(
        dumps({
            'address': ipv4_address,
            'netmask': '255.255.255.255',
            'partition_list': partition_list,
            'reference': self._computer_id,
            'instance_root': self._instance_root,
            'software_root': self._software_root
        }))

    for part in unknown_partition_set:
      self._logger.debug(
          "removing partition no longer part of format spec %s", part)
      # remove partition directory
      rmtree(part)
      # remove partition supervisor config, if it was not removed cleanly
      supervisor_conf = os.path.join(
          self._instance_root,
          'etc',
          'supervisord.conf.d',
          '%s.conf' % os.path.basename(part))
      if os.path.exists(supervisor_conf):
        self._logger.info(
          "removing leftover supervisor config from destroyed partition at %s",
          supervisor_conf)
        os.unlink(supervisor_conf)

    # update slapformat configuration
    old_partition_count = self._partition_count
    self._partition_count = partition_count
    self._partition_base_name = partition_base_name
    self._ipv4_address = ipv4_address
    self._ipv6_address = ipv6_address
    if old_partition_count != partition_count:
      SlapOSConfigWriter(self).writeConfig(self._slapos_config)
    SlapformatDefinitionWriter(self).writeConfig(self._slapformat_definition)

  def supply(self, software_url, computer_guid=None, state="available"):
    """Supply a software, see ISupply.supply

    Software can only be supplied on this embedded computer.
    """
    if computer_guid not in (None, self._computer_id):
      raise ValueError("Can only supply on embedded computer")
    self._slap.registerSupply().supply(
        software_url,
        self._computer_id,
        state=state,
    )

  def request(
      self,
      software_release,
      partition_reference,
      software_type=None,
      shared=False,
      partition_parameter_kw=None,
      filter_kw=None,
      state=None):
    """Request an instance, see IRequester.request

    Instance can only be requested on this embedded computer.
    """
    if filter_kw is not None:
      raise ValueError("Can only request on embedded computer")
    return self._slap.registerOpenOrder().request(
        software_release,
        software_type=software_type,
        partition_reference=partition_reference,
        shared=shared,
        partition_parameter_kw=partition_parameter_kw,
        filter_kw=filter_kw,
        state=state)

  def start(self):
    """Start the system.

    If system was stopped, it will start partitions.
    If system was already running, this does not restart partitions.
    """
    self._logger.debug("Starting StandaloneSlapOS in %s", self._base_directory)
    self._ensureSupervisordStarted()
    self._ensureSlapOSAvailable()

  def stop(self, timeout=300):
    # type: (int) -> None
    """Stops all services.

    This methods blocks until the services are stopped or the timeout is reached.

    Arguments:
      * `timeout`: maximum duration, in seconds, to wait for services to
      terminate.

    Error cases:
      * `RuntimeError` when unexpected error occurs trying to stop supervisors.
    """
    self._logger.info("shutting down")

    with self.system_supervisor_rpc as system_supervisor:
      system_supervisor_process = psutil.Process(system_supervisor.getPID())
      system_supervisor.stopAllProcesses()
      system_supervisor.shutdown()
    _, alive = psutil.wait_procs([system_supervisor_process], timeout=timeout)
    if alive:
      raise RuntimeError(
          "Could not terminate some processes: {}".format(alive))

  def waitForSoftware(self, max_retry=0, debug=False, error_lines=30, install_all=False):
    """Synchronously install or uninstall all softwares previously supplied/removed.

    This method retries on errors. If after `max_retry` times there's
    still an error, the error is raised, containing `error_lines` of output
    from the buildout command.

    If `debug` is true, buildout is executed in the foreground, with flags to
    drop in a debugger session if error occurs.

    If `install_all` is true, all softwares will be installed, even the ones
    for which the installation was already completed. This is equivalent to
    running `slapos node software --all`.

    Error cases:
      * `SlapOSNodeSoftwareError` when buildout error while installing software.
      * Unexpected `Exception` if unable to connect to embedded slap server.
    """
    try:
        return self._runSlapOSCommand(
            'slapos-node-software-all' if install_all else 'slapos-node-software',
            max_retry=max_retry,
            debug=debug,
            error_lines=error_lines,
        )
    except SlapOSNodeCommandError as e:
        raise SlapOSNodeSoftwareError(*e.args)

  def waitForInstance(self, max_retry=0, debug=False, error_lines=30):
    """Instantiate all partitions previously requested for start.

    This method retries on errors. If after `max_retry` times there's
    still an error, the error is raised, containing `error_lines` of output
    from the buildout command.

    If `debug` is true, buildout is executed in the foreground, with flags to
    drop in a debugger session if error occurs.

    Error cases:
      * `SlapOSNodeInstanceError` when buildout error while creating instances.
      * Unexpected `Exception` if unable to connect to embedded slap server.
    """
    try:
        return self._runSlapOSCommand(
            'slapos-node-instance-all' if self._force_slapos_node_instance_all else 'slapos-node-instance',
            max_retry=max_retry,
            debug=debug,
            error_lines=error_lines,
        )
    except SlapOSNodeCommandError as e:
        raise SlapOSNodeInstanceError(*e.args)

  def waitForReport(self, max_retry=0, debug=False, error_lines=30):
    """Destroy all partitions previously requested for destruction.

    This method retries on errors. If after `max_retry` times there's
    still an error, the error is raised, containing `error_lines` of output
    from the buildout command.

    If `debug` is true, buildout is executed in the foreground, with flags to
    drop in a debugger session if error occurs.

    Error cases:
      * `SlapOSNodeReportError` when buildout error while destroying instances.
      * Unexpected `Exception` if unable to connect to embedded slap server.
    """
    try:
        return self._runSlapOSCommand(
            'slapos-node-report',
            max_retry=max_retry,
            debug=debug,
            error_lines=error_lines,
        )
    except SlapOSNodeCommandError as e:
        raise SlapOSNodeReportError(*e.args)

  def _runSlapOSCommand(
      self, command, max_retry=0, debug=False, error_lines=30):
    if debug:
      prog = self._slapos_commands[command]
      # used in format(**locals()) below
      debug_args = prog.get('debug_args', '')  # pylint: disable=unused-variable
      command = prog['command'].format(**locals())
      try:
        return subprocess.check_call(
            command,
            shell=True,
        )
      except subprocess.CalledProcessError as e:
        if e.returncode == SLAPGRID_PROMISE_FAIL:
          self._logger.exception('Promise error when running %s', command)
          import pdb; pdb.post_mortem()
        raise SlapOSNodeCommandError({
            'output': 'No output available in debug mode',
            'exitstatus': e.returncode,
        })
    with self.system_supervisor_rpc as supervisor:
      retry = 0
      while True:
        self._logger.info("starting command %s (retry:%s)", command, retry)
        supervisor.startProcess(command, False)

        delay = 0.1
        while True:
          self._logger.debug("retry %s: sleeping %s", retry, delay)
          # we start waiting a short delay and increase the delay each loop,
          # because when software is already built, this should return fast,
          # but when we build a full software we don't need to poll the
          # supervisor too often.
          time.sleep(delay)
          delay = min(delay * 1.2, 300)
          process_info = supervisor.getProcessInfo(command)
          if process_info['statename'] in ('EXITED', 'FATAL'):
            self._logger.debug("SlapOS command finished %s" % process_info)
            if process_info['exitstatus'] == 0:
              return
            if retry >= max_retry:
              # get the last lines of output, at most `error_lines`. If
              # these lines are long, the output may be truncated.
              _, log_offset, _ = supervisor.tailProcessStdoutLog(command, 0, 0)
              output, _, _ = supervisor.tailProcessStdoutLog(
                  command, log_offset - (2 << 13), 2 << 13)
              raise SlapOSNodeCommandError({
                  'output': '\n'.join(output.splitlines()[-error_lines:]),
                  'exitstatus': process_info['exitstatus'],
              })
            break
        retry += 1

  def _ensureSupervisordStarted(self):
    if os.path.exists(self._supervisor_pid):
      with open(self._supervisor_pid, 'r') as f:
        try:
          pid = int(f.read())
        except (ValueError, TypeError):
          self._logger.debug(
              "Error reading supervisor pid from file, assuming it's not running"
          )
        else:
          try:
            process = psutil.Process(pid)
          except psutil.NoSuchProcess:
            pass
          else:
            if process.name() == 'supervisord':
              # OK looks already running
              self._logger.debug("Supervisor running with pid %s", pid)
              return
          self._logger.debug("Supervisor pid file seem stale")
    # start new supervisord
    output = subprocess.check_output(
        ['supervisord', '--configuration', self._supervisor_config],
        cwd=self._base_directory,
    )
    self._logger.debug("Started new supervisor: %s", output)

  def _isSlapOSAvailable(self):
    try:
      urllib.request.urlopen(self._master_url).close()
    except urllib.error.HTTPError as e:
      # root URL (/) of slapproxy is 404
      if e.code == http_client.NOT_FOUND:
        return True
      raise
    except urllib.error.URLError as e:
      if e.reason.errno == errno.ECONNREFUSED:
        return False
      raise
    except socket.error as e:
      if e.errno == errno.ECONNRESET:
        return False
      raise
    except http_client.HTTPException:
      return False
    return True  # (if / becomes 200 OK)

  def _ensureSlapOSAvailable(self):
    # Wait for proxy to accept connections
    for i in range(2**8):
      if self._isSlapOSAvailable():
        return
      time.sleep(i * .01)
    raise RuntimeError("SlapOS not started")
