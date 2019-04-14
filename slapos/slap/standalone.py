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
import shutil

from six.moves import urllib
from six.moves import http_client

try:
  import subprocess32 as subprocess
except ImportError:
  import subprocess

import xml_marshaller
import zope.interface
import psutil

from .interface.slap import IException
from .interface.slap import ISupply
from .interface.slap import IRequester

from .slap import slap
from ..grid.svcbackend import getSupervisorRPC


@zope.interface.implementer(IException)
class SlapOSNodeCommandError(Exception):
  """Exception raised when running a SlapOS Node command failed.
  """

  def __str__(self):
    return "{} exitstatus: {} output:\n{}".format(
        self.__class__.__name__,
        self.args[0]['exitstatus'],
        self.args[0]['output'],
    )


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
        stdout_logfile_backups = 10

    """.format(**locals()))

  def _getSupervisorConfigParts(self):
    """Iterator on parts of formatted config.
    """
    standalone_slapos = self._standalone_slapos
    pid = os.getpid()
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

        [rpcinterface:supervisor]
        supervisor.rpcinterface_factory = supervisor.rpcinterface:make_main_rpcinterface

        [program:slapos-proxy]
        command = slapos proxy start --cfg {standalone_slapos._slapos_config} --verbose
        startretries = 0
        startsecs = 0
        redirect_stderr = true

        [program:standalone-auto-shutdown]
        command = python {standalone_slapos._auto_shutdown_script} {pid} {standalone_slapos._slapos_config} {standalone_slapos._supervisor_config}
        startretries = 0
        startsecs = 0
        redirect_stderr = true
        """.format(**locals()))

    for program, program_config in standalone_slapos._slapos_commands.items():
      yield self._getProgramConfig(
          program,
          program_config['command'].format(
              self=standalone_slapos, debug_args=''),
          stdout_logfile=program_config.get(
              'stdout_logfile', 'AUTO').format(self=standalone_slapos))

  def writeConfig(self, path):
    if os.path.exists(path):
      os.remove(path)
    tmp_path = "{}-{}".format(path, os.getpid())
    with open(tmp_path, 'w') as f:
      for part in self._getSupervisorConfigParts():
        f.write(part)
      # ensure this is written to disk, for "reattach" scenario where we tell
      # supervisor to re-read its config.
      f.flush()
      os.fsync(f.fileno())
    os.rename(tmp_path, path)
    self._standalone_slapos._logger.debug("updated configfile %s !", os.getpid())


class SlapOSConfigWriter(ConfigWriter):
  """Write slapos configuration at etc/slapos.cfg
  """

  def writeConfig(self, path):
    standalone_slapos = self._standalone_slapos
    with open(path, 'w') as f:
      f.write(
          textwrap.dedent(
              """
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
      f.write(
          textwrap.dedent(
              """\
              #!/bin/sh
              SLAPOS_CONFIGURATION={self._standalone_slapos._slapos_config} \\
              SLAPOS_CLIENT_CONFIGURATION=$SLAPOS_CONFIGURATION \\
              exec slapos "$@"
      """.format(**locals())))
    os.chmod(path, 0o755)


class AutoShutownScriptWriter(ConfigWriter):
  """Write an etc/standalone_auto_shutdown.py script.

  This script is responisble for watching that the process to which this
  StandaloneSlapOS is attached is still running. If process is no longer
  running, this script stops the StandaloneSlapOS.
  """

  def writeConfig(self, path):
    with open(path, 'w') as f:
      f.write(
          textwrap.dedent(
              """\
          #!/usr/bin/env python
          from __future__ import print_function
          import os
          import sys
          import time
          import subprocess
          from datetime import datetime

          monitored_pid = int(sys.argv[1])
          slapos_config_file = sys.argv[2]
          supervisor_config_file = sys.argv[3]

          import signal
          def sigterm_handler(_signo, _stack_frame):
              print (str(datetime.now()), os.getpid(), "Got signal", _signo)
              sys.exit(0)
          signal.signal(signal.SIGTERM, sigterm_handler)

          def isAlive(pid):
            try:
              os.kill(pid, 0)
            except OSError:
              return False
            return True

          print (str(datetime.now()), os.getpid(), "Watching PID", monitored_pid)
          while True:
            print (str(datetime.now()), os.getpid(), "loop watching", monitored_pid)
            if not isAlive(monitored_pid):
              print (str(datetime.now()), os.getpid(), "Process is no longer alive, terminating")
              subprocess.call(['slapos', 'node', 'stop', '--cfg', slapos_config_file, 'all'])
              subprocess.call(['slapos', 'node', 'supervisorctl', '--cfg', slapos_config_file, 'shutdown'])
              subprocess.call(['supervisorctl', '-c', supervisor_config_file, 'stop', 'all'])
              subprocess.call(['supervisorctl', '-c', supervisor_config_file, 'shutdown'])
              break
            time.sleep(1)
          """))


@zope.interface.implementer(ISupply, IRequester)
class StandaloneSlapOS(object):
  """A SlapOS that can be embedded in other applications, also useful for testing.

  This plays the role of an `IComputer` where users of classes implementing this
  interface can install software, create partitions and access parameters of the
  running partitions.

  Extends the existing `IRequester` and `ISupply`, with the special behavior that
  `IRequester.request` and `ISupply.supply` will only use the embedded computer.
  """

  def __init__(
      self, base_directory, server_ip, server_port, computer_id='local'):
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
        'slapos-node-software':
            {
                'command':
                    'slapos node software --cfg {self._slapos_config} --all {debug_args}',
                'debug_args':
                    '--buildout-debug',
                'stdout_logfile':
                    '{self._log_directory}/slapos-node-software.log',
            },
        'slapos-node-instance':
            {
                'command':
                    'slapos node instance --cfg {self._slapos_config} --all {debug_args}',
                'debug_args':
                    '--buildout-debug',
                'stdout_logfile':
                    '{self._log_directory}/slapos-node-instance.log',
            },
        'slapos-node-report':
            {
                'command':
                    'slapos node report --cfg {self._slapos_config} {debug_args}',
                'log_file':
                    '{self._log_directory}/slapos-node-report.log',
            },
    }
    self._computer_id = computer_id
    self._slap = slap()
    self._slap.initializeConnection(self._master_url)

    self._initBaseDirectory()


  def _initBaseDirectory(self):
    """Create the directory after checking it's not too deep.
    """
    base_directory = self._base_directory
    # To prevent error: Cannot open an HTTP server: socket.error reported
    # AF_UNIX path too long This `base_directory` should not be too deep.
    # Socket path is 108 char max on linux
    # https://github.com/torvalds/linux/blob/3848ec5/net/unix/af_unix.c#L234-L238
    # Supervisord socket name contains the pid number, which is why we add
    # .xxxxxxx in this check.
    if len(os.path.join(base_directory, 'supervisord.socket.xxxxxxx')) > 108:
      raise PathTooDeepError(
          'working directory ( {base_directory} ) is too deep'.format(
              **locals()))

    def ensureDirectoryExists(d):
      if not os.path.exists(d):
        os.mkdir(d)

    self._software_root = os.path.join(base_directory, 'soft')
    ensureDirectoryExists(self._software_root)
    os.chmod(self._software_root, 0o750)
    self._instance_root = os.path.join(base_directory, 'inst')
    ensureDirectoryExists(self._instance_root)
    os.chmod(self._instance_root, 0o750)

    etc_directory = os.path.join(base_directory, 'etc')
    ensureDirectoryExists(etc_directory)
    self._supervisor_config = os.path.join(etc_directory, 'supervisord.conf')
    self._slapos_config = os.path.join(etc_directory, 'slapos.cfg')
    self._auto_shutdown_script = os.path.join(
        etc_directory, 'standalone_auto_shutdown.py')

    var_directory = os.path.join(base_directory, 'var')
    ensureDirectoryExists(var_directory)
    self._proxy_database = os.path.join(var_directory, 'proxy.db')

    # for convenience, make a slapos command for this instance
    bin_directory = os.path.join(base_directory, 'bin')
    ensureDirectoryExists(bin_directory)

    self._slapos_bin = os.path.join(bin_directory, 'slapos')

    self._log_directory = os.path.join(var_directory, 'log')
    ensureDirectoryExists(self._log_directory)
    self._supervisor_log = os.path.join(self._log_directory, 'supervisord.log')

    run_directory = os.path.join(var_directory, 'run')
    ensureDirectoryExists(run_directory)
    self._supervisor_pid = os.path.join(run_directory, 'supervisord.pid')
    self._software_pid = os.path.join(run_directory, 'slapos-node-software.pid')
    self._instance_pid = os.path.join(run_directory, 'slapos-node-instance.pid')
    self._report_pid = os.path.join(run_directory, 'slapos-node-report.pid')

    self._supervisor_socket = os.path.join(run_directory, 'supervisord.sock')

    # debug
    handler = logging.FileHandler(
        os.path.join(self._log_directory, 'standalone-%s.log' % os.getpid()))
    handler.setFormatter(
        logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    self._logger.addHandler(handler)
    self._logger.setLevel(logging.DEBUG)

    self._logger.propagate = True
    self._logger.debug("Go !")

    SupervisorConfigWriter(self).writeConfig(self._supervisor_config)
    SlapOSConfigWriter(self).writeConfig(self._slapos_config)
    SlapOSCommandWriter(self).writeConfig(self._slapos_bin)
    AutoShutownScriptWriter(self).writeConfig(self._auto_shutdown_script)

    self.start()

  @property
  def computer(self):
    """Access the computer.
    """
    return self._slap.registerComputer(self._computer_id)

  @property
  def software_directory(self):
    # type: str
    """Path to software directory
    """
    return self._software_root

  @property
  def instance_directory(self):
    # type: str
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
    return getSupervisorRPC(
        # this socket path is not configurable.
        os.path.join(self._instance_root, "supervisord.socket"))

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
      partition_list.append(
          {
              'address_list':
                  [
                      {
                          'addr': ipv4_address,
                          'netmask': '255.255.255.255'
                      },
                      {
                          'addr': ipv6_address,
                          'netmask': 'ffff:ffff:ffff::'
                      },
                  ],
              'path':
                  partition_path,
              'reference':
                  partition_reference,
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
        part_id = os.path.basename(part)
        computer_partition = computer_partition_dict.get(os.path.basename(part))
        if computer_partition is not None \
             and computer_partition.getState() != "destroyed":
          raise ValueError(
              "Cannot reformat to remove busy partition at {part}".format(
                  **locals()))

    self.computer.updateConfiguration(
        xml_marshaller.xml_marshaller.dumps(
            {
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
      shutil.rmtree(part)

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
    self._logger.info(
        "Started StandaloneSlapOS in %s, attached to %s", self._base_directory,
        os.getpid())

  def stop(self):
    """Stops all services.

    This methods blocks until services are stopped or a timeout is reached.

    Error cases:
      * `Exception` when unexpected error occurs trying to stop supervisors.
    """
    self._logger.info("shutting down")

    # shutdown slapos node instance supervisor, if it has been created.
    instance_process_alive = []
    if os.path.exists(os.path.join(self._instance_root, 'etc',
                                   'supervisord.conf')):
      try:
        with self.instance_supervisor_rpc as instance_supervisor:
          instance_supervisor_process = psutil.Process(
              instance_supervisor.getPID())
          instance_supervisor.stopAllProcesses()
          instance_supervisor.shutdown()
          # shutdown returns before process is completly stopped,
          # so wait for process.
          _, instance_process_alive = psutil.wait_procs(
              [instance_supervisor_process], timeout=10)
      except BaseException as e:
        self._logger.info("Ignoring exception while stopping instances: %s", e)

    with self.system_supervisor_rpc as system_supervisor:
      system_supervisor_process = psutil.Process(system_supervisor.getPID())
      system_supervisor.stopAllProcesses()
      system_supervisor.shutdown()
    _, alive = psutil.wait_procs([system_supervisor_process], timeout=10)
    if alive + instance_process_alive:
      raise RuntimeError(
          "Could not terminate some processes: {}".format(
              alive + instance_process_alive))

  def detach(self):
    """By default, StandaloneSlapOS will automatically stop when the process which
    started it is no longer alive, calling `detach` disable this behavior. After
    detaching, the process will no longer be watched.
    """
    with self.system_supervisor_rpc as supervisor:
      orig_state = state = supervisor.getProcessInfo('standalone-auto-shutdown')
      self._logger.debug("detaching, standalone-auto-shutdown state: %s", state)
      if state['statename'] in ('RUNNING', 'STARTING'):
        self._logger.debug("stopping standalone-auto-shutdown")
        supervisor.stopProcess('standalone-auto-shutdown')
        state = supervisor.getProcessInfo('standalone-auto-shutdown')
        self._logger.debug("after stop: standalone-auto-shutdown state: %s", state)
        try:
          proc =psutil.Process(orig_state['pid'])
          self._logger.debug("ahah proc is %s", proc)
        except:
          self._logger.exception("psutil of standalone-auto-shutdown")

  def reattach(self):
    """Reattach a detached StandaloneSlapOS
    """
    # standalone-auto-shutdown should have changed, because config file was re-generated
    # for a new pid.
    self._logger.info("reattaching to %s", os.getpid())
    with self.system_supervisor_rpc as supervisor:
      state = supervisor.getProcessInfo('standalone-auto-shutdown')
      self._logger.debug(
          "reattaching, standalone-auto-shutdown state: %s", state)
      if state['statename'] in ('RUNNING', 'STARTING'):
        self._logger.debug("stopping standalone-auto-shutdown")
        supervisor.stopProcessGroup('standalone-auto-shutdown')

      (added, changed, removed), = supervisor.reloadConfig()
      assert not added
      assert not removed
      assert changed == ['standalone-auto-shutdown']
      self._logger.debug("removing/adding standalone-auto-shutdown")
      supervisor.removeProcessGroup('standalone-auto-shutdown')
      supervisor.addProcessGroup('standalone-auto-shutdown')
      self._logger.debug("starting standalone-auto-shutdown")
      supervisor.startProcessGroup('standalone-auto-shutdown')

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

  def _runSlapOSCommand(
      self, command, max_retry=0, debug=False, error_lines=30):
    success = False
    if debug:
      prog = self._slapos_commands[command]
      debug_args = prog.get('debug_args', '')
      return subprocess.check_call(
          prog['command'].format(**locals()), shell=True)

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
              raise SlapOSNodeCommandError(
                  {
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
          process = psutil.Process(pid)
          if process.name() == 'supervisord':
            # OK looks already running
            self._logger.debug("Supervisor running with pid %s", pid)
            return
          self._logger.debug("Supervisor pid file seem stale")
    # start new supervisord
    output = subprocess.check_output(
        ['supervisord'],
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
