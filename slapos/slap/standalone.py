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

import os
import textwrap
import hashlib
import logging
import time
import sys
import errno
import socket

from six.moves import xmlrpc_client as xmlrpclib
from six.moves import urllib
from six.moves import http_client

try:
  import subprocess32 as subprocess
except ImportError:
  import subprocess

import xml_marshaller
import zope.interface
import supervisor.xmlrpc
import psutil

from .interface.slap import IException
from .interface.slap import ISupply
from .interface.slap import IRequester
from .interface.slap import IStandaloneSlapOS

from .slap import slap
from .slap import Supply
from .slap import ConnectionError
from ..grid.svcbackend import getSupervisorRPC


@zope.interface.implementer(IException)
class SlapOSNodeCommandError(Exception):
  """Exception raised when running a SlapOS Node command failed.
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
  def _getProgramConfig(self, program_name, command):
    """Format a supervisor program block.
    """
    return textwrap.dedent("""\
        [program:{program_name}]
        command = {command}
        autostart = false
        autorestart = false
        startretries = 1
        redirect_stderr = true
        stdout_logfile_maxbytes = 5MB
        stdout_logfile_backups = 10

    """.format(**locals()))

  def _getSupervisorConfigParts(self):
    """Iterator on parts of formatted config.
    """
    standalone_slapos = self._standalone_slapos
    yield textwrap.dedent("""
        [unix_http_server]
        file = {standalone_slapos._supervisor_socket}

        [supervisorctl]
        serverurl = unix://{standalone_slapos._supervisor_socket}

        [supervisord]
        logfile = {standalone_slapos._supervisor_log}
        pidfile = {standalone_slapos._supervisor_pid}

        [rpcinterface:supervisor]
        supervisor.rpcinterface_factory = supervisor.rpcinterface:make_main_rpcinterface

        [program:slapos-proxy]
        command = slapos proxy start --cfg {standalone_slapos._slapos_config} --verbose

      """.format(**locals()))

    for program, program_config in standalone_slapos._slapos_commands.items():
      yield self._getProgramConfig(program, program_config['command'].format(
          self=standalone_slapos,
          debug_args='',
      ))

  def writeConfig(self, path):
    with open(path, 'w') as f:
      for part in self._getSupervisorConfigParts():
        f.write(part)


class SlapOSConfigWriter(ConfigWriter):
  """Write slapos configuration at etc/slapos.cfg
  """
  def writeConfig(self, path):
    standalone_slapos = self._standalone_slapos
    with open(path, 'w') as f:
      f.write(textwrap.dedent("""
        [slapos]
        software_root = {standalone_slapos._software_root}
        instance_root = {standalone_slapos._instance_root}
        master_url = {standalone_slapos._master_url}
        computer_id = {standalone_slapos._computer_id}
        root_check = False
        pidfile_software = {standalone_slapos._instance_pid}
        pidfile_instance = {standalone_slapos._software_pid}
        pidfile_report =  {standalone_slapos._report_pid}

        [slapproxy]
        host = {standalone_slapos._server_ip}
        port = {standalone_slapos._server_port}
        database_uri = {standalone_slapos._proxy_database}
        """.format(**locals())))


class SlapOSCommandWriter(ConfigWriter):
  """Write a bin/slapos wrapper.
  """
  def writeConfig(self, path):
    with open(path, 'w') as f:
      f.write(textwrap.dedent("""\
        #!/bin/sh
        SLAPOS_CONFIGURATION={self._standalone_slapos._slapos_config} \\
        SLAPOS_CLIENT_CONFIGURATION=$SLAPOS_CONFIGURATION \\
        exec slapos "$@"
      """.format(**locals())))
    os.chmod(path, 0o755)


@zope.interface.implementer(IStandaloneSlapOS, ISupply, IRequester)
class StandaloneSlapOS(object):
  """A SlapOS that can be embedded in other applications, also useful for testing.

  This plays the role of an `IComputer` where users of classes implementing this
  interface can install software, create partitions and access parameters of the
  running partitions.

  Extends the existing `IRequester` and `ISupply`, with the special behavior that
  `IRequester.request` and `ISupply.supply` will only use the embedded computer.

  """
  def __init__(self, base_directory, server_ip, server_port, computer_id='local'):
    """Constructor, creates a standalone slapos in `base_directory`.

    Arguments:
      * `base_directory`  -- the directory which will contain softwares and instances.
      * `server_ip`, `server_port` -- the address this SlapOS proxy will listen to.
      * `computer_id` -- the id of this computer.

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

    self._base_directory = base_directory

    self._slapos_commands = {
      'slapos-node-software': {
        'command': 'slapos node software --cfg {self._slapos_config} --all {debug_args}',
        'debug_args': '--buildout-debug',
      },
      'slapos-node-instance': {
        'command': 'slapos node instance --cfg {self._slapos_config} --all {debug_args}',
        'debug_args': '--buildout-debug',
      },
      'slapos-node-report': {
        'command': 'slapos node report --cfg {self._slapos_config} {debug_args}',
        'debug_args': '',
      }
    }
    self._computer_id = computer_id
    self._computer = None
    self._slap = slap()
    self._slap.initializeConnection(self._master_url)

    self._initBaseDirectory()

  def _initBaseDirectory(self):
    """Create the directory after checking it's not too deep.
    """
    base_directory = self._base_directory
    self._software_root = os.path.join(base_directory, 'soft')
    self._instance_root = os.path.join(base_directory, 'inst')

    # To prevent error: Cannot open an HTTP server: socket.error reported
    # AF_UNIX path too long This `working_directory` should not be too deep.
    # Socket path is 108 char max on linux
    # https://github.com/torvalds/linux/blob/3848ec5/net/unix/af_unix.c#L234-L238
    # Supervisord socket name contains the pid number, which is why we add
    # .xxxxxxx in this check.
    if len(os.path.join(self._instance_root, 'supervisord.socket.xxxxxxx')) > 108:
      raise PathTooDeepError(
        'working directory ( {base_directory} ) is too deep'.format(**locals()))

    if not os.path.exists(base_directory):
      os.mkdir(base_directory)

    etc_directory = os.path.join(base_directory, 'etc')
    if not os.path.exists(etc_directory):
      os.mkdir(etc_directory)
    self._supervisor_config = os.path.join(etc_directory, 'supervisord.conf')
    self._slapos_config = os.path.join(etc_directory, 'slapos.cfg')

    var_directory = os.path.join(base_directory, 'var')
    if not os.path.exists(var_directory):
      os.mkdir(var_directory)
    self._proxy_database = os.path.join(var_directory, 'proxy.db')

    # for convenience, make a slapos command for this instance
    bin_directory = os.path.join(base_directory, 'bin')
    if not os.path.exists(bin_directory):
      os.mkdir(bin_directory)
    self._slapos_bin = os.path.join(bin_directory, 'slapos')

    log_directory = os.path.join(var_directory, 'log')
    if not os.path.exists(log_directory):
      os.mkdir(log_directory)
    self._supervisor_log = os.path.join(log_directory, 'supervisord.log')

    run_directory = os.path.join(var_directory, 'run')
    if not os.path.exists(run_directory):
      os.mkdir(run_directory)
    self._supervisor_pid = os.path.join(run_directory, 'supervisord.pid')
    self._software_pid = os.path.join(run_directory, 'slapos-node-software.pid')
    self._instance_pid = os.path.join(run_directory, 'slapos-node-instance.pid')
    self._report_pid = os.path.join(run_directory, 'slapos-node-report.pid')

    self._supervisor_socket = os.path.join(run_directory, 'supervisord.sock')

    SupervisorConfigWriter(self).writeConfig(self._supervisor_config)
    SlapOSConfigWriter(self).writeConfig(self._slapos_config)
    SlapOSCommandWriter(self).writeConfig(self._slapos_bin)

    self.start()

  @property
  def computer(self):
    """Access the computer.
    """
    if self._computer is None:
      self._computer = self._slap.registerComputer(self._computer_id)
    return self._computer

  @property
  def software_directory(self):
    """Path to software directory
    """
    return self._software_root

  @property
  def instance_directory(self):
    """Path to instance directory
    """
    return self._instance_root

  @property
  def supervisor_rpc(self):
    """A xmlrpc connection to control supervisor, use as a context manager.
    """
    return getSupervisorRPC(self._supervisor_socket)

  def format(
      self,
      partition_count,
      ipv4_address,
      ipv6_address,
      partition_base_name="slappart"):
    """Creates `partition_count` partitions.

    All partitions have the same `ipv4_address` and `ipv6_address` and
    use the current system user.
    """
    for path in (
      self._software_root,
      self._instance_root, ):
      if not os.path.exists(path):
        os.mkdir(path)

    # create partitions and configure computer
    partition_list = []
    for i in range(partition_count):
      partition_reference = '%s%s' % ( partition_base_name, i )

      partition_path = os.path.join(self._instance_root, partition_reference)
      if not(os.path.exists(partition_path)):
        os.mkdir(partition_path)
      os.chmod(partition_path, 0o750)
      partition_list.append({
          'address_list': [
             {'addr': ipv4_address,
              'netmask': '255.255.255.255'},
             {'addr': ipv6_address,
              'netmask': 'ffff:ffff:ffff::'},],
          'path': partition_path,
          'reference': partition_reference,
          'tap': {'name': partition_reference},})

    self.computer.updateConfiguration(
        xml_marshaller.xml_marshaller.dumps({
           'address': ipv4_address,
           'netmask': '255.255.255.255',
           'partition_list': partition_list,
           'reference': self._computer_id,
           'instance_root': self._instance_root,
           'software_root': self._software_root}))

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

  def request(self, software_release, software_type, partition_reference,
              shared=False, partition_parameter_kw=None, filter_kw=None, state=None):
    """Request an instance, see IRequester.request

    Instance can only be requested on this embedded computer.
    """
    if filter_kw is not None:
      raise ValueError("Can only request on embedded computer")
    if shared:
      raise ValueError("Can not request shared instances")
    return self._slap.registerOpenOrder().request(
        software_release,
        software_type=software_type,
        partition_reference=partition_reference,
        shared=shared,
        partition_parameter_kw=partition_parameter_kw,
        filter_kw=filter_kw,
        state=state
    )

  def start(self):
    """Start the system.

    If system was stopped, it will start partitions.
    If system was already running, this does not restart partitions.
    """
    self._ensureSupervisordStarted()
    self._ensureSlapOSAvailable()

  def stop(self):
    """Stops all services.

    This methods blocks until services are stop or a timeout is reached.

    Error cases:
      * `RuntimeError` when supervisor refuses to stops.
    """
    self._logger.debug("shutting down")

    with self.supervisor_rpc as supervisor:
      supervisor.shutdown()
    # wait for slap proxy to be stopped
    for i in range(30):
      if self._isSlapOSAvailable():
        time.sleep(.2 * i)
      else:
        break
    # wait for supervisor to remove its pid file
    for i in range(30):
      if not os.path.exists(self._supervisor_pid):
        return
      time.sleep(.2 * i)
    raise RuntimeError("Shutdown failed")

  def waitForSoftware(self, max_retry=0, debug=False, error_lines=30):
    """Synchronously install or uninstall all softwares previously supplied/removed.

    This method retries on errors. If after `max_retry` times there's
    still an error, the error is raised, containing `error_lines` of output
    from the buildout command.

    If `debug` is true, buildout is executed in the foreground, with flags to
    drop in a debugger session if error occurs.

    Error cases:
      * `SlapOSNodeCommandError` when buildout error while installing software.
      * Unexpected `Exception` if unable to connect to embedded slap server.

    """
    return self._runSlapOSCommand(
        'slapos-node-software',
        max_retry=max_retry,
        debug=debug,
    )

  def waitForInstance(self, max_retry=0, debug=False, error_lines=30):
    """Instantiate all partitions previously requested for start.

    This method retries on errors. If after `max_retry` times there's
    still an error, the error is raised, containing `error_lines` of output
    from the buildout command.

    If `debug` is true, buildout is executed in the foreground, with flags to
    drop in a debugger session if error occurs.

    Error cases:
      * `SlapOSNodeCommandError` when buildout error while installing software.
      * Unexpected `Exception` if unable to connect to embedded slap server.
    """
    return self._runSlapOSCommand(
        'slapos-node-instance',
        max_retry=max_retry,
        debug=debug,
    )

  def waitForReport(self, max_retry=0, debug=False, error_lines=30):
    """Destroy all partitions previously requested for destruction.

    This method retries on errors. If after `max_retry` times there's
    still an error, the error is raised, containing `error_lines` of output
    from the buildout command.

    If `debug` is true, buildout is executed in the foreground, with flags to
    drop in a debugger session if error occurs.

    Error cases:
      * `SlapOSNodeCommandError` when buildout error while installing software.
      * Unexpected `Exception` if unable to connect to embedded slap server.
    """
    return self._runSlapOSCommand(
        'slapos-node-report',
        max_retry=max_retry,
        debug=debug,
    )

  def _runSlapOSCommand(self, command, max_retry=0, debug=False, error_lines=30):
    success = False
    if debug:
      prog = self._slapos_commands[command]
      debug_args = prog.get('debug_args', '')
      return subprocess.check_call(
          prog['command'].format(**locals()),
          shell=True)

    with self.supervisor_rpc as supervisor:
      retry = 0
      while True:
        self._logger.debug("retry %s: starting %s", retry, command)
        supervisor.startProcess(command, False)

        delay = 0.5
        while True:
          self._logger.debug("retry %s: sleeping %s", retry, delay)
          # we start waiting a short delay and increase the delay each loop,
          # because when software is already built, this should return fast,
          # but when we build a full software we don't need to poll the
          # supervisor too often.
          time.sleep(delay)
          delay = min(delay * 1.2, 30)
          process_info = supervisor.getProcessInfo(command)
          if process_info['statename'] in ('EXITED', 'FATAL'):
            self._logger.debug("SlapOS command finished %s" % process_info)
            if process_info['exitstatus'] == 0:
              return
            if retry >= max_retry:
              # get the last lines of output, at most `error_lines`. If
              # these lines are long, the output may be truncated.
              _, log_offset,  _ = supervisor.tailProcessStdoutLog(
                  command, 0, 0)
              output, _, _ = supervisor.tailProcessStdoutLog(
                command, log_offset-(2 << 13), 2 << 13)
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
        except (ValueError, TypeError) as e:
          self._logger.debug(
            "Error reading supervisor pid from file, assuming it's not running")
        else:
          process = psutil.Process(pid)
          if process.name() == 'supervisord':
            # OK looks already running
            self._logger.debug(
              "Supervisor running with pid %s", pid)
            return
          self._logger.debug(
              "Supervisor pid file seem stale")

    # start new supervisord
    output = subprocess.check_output(
        ['supervisord'],
        cwd=self._base_directory,
    )
    self._logger.debug(
        "Started new supervisor: %s", output)

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
    return True # (if / becomes 200 OK)

  def _ensureSlapOSAvailable(self):
    # Wait for proxy to accept connections
    retry = 0
    for i in range(30):
      if self._isSlapOSAvailable():
        return
      time.sleep(i * .2)
      if retry >= 60:
        raise RuntimeError("SlapOS not started")
