# -*- coding: utf-8 -*-
# vim: set et sts=2:
##############################################################################
#
# Copyright (c) 2010, 2011, 2012 Vifib SARL and Contributors.
# All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsibility of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# guarantees and support are strongly advised to contract a Free Software
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
import pkg_resources
import socket as socketlib
import subprocess
import stat
import sys
import time
from six.moves import xmlrpc_client as xmlrpclib
import contextlib

from slapos.grid.utils import (createPrivateDirectory, SlapPopen, updateFile)
from slapos.util import bytes2str

from supervisor import xmlrpc, states


@contextlib.contextmanager
def getSupervisorRPC(socket):
  """Get a supervisor XML-RPC connection.

  Use in a context manager for proper closing of sockets.
  """
  supervisor_transport = xmlrpc.SupervisorTransport('', '',
      'unix://' + socket)
  server_proxy = xmlrpclib.ServerProxy('http://127.0.0.1',
      supervisor_transport)

  # python3's xmlrpc is a closing context manager, python2 is not and cannot be
  # just used as a context manager as it would call __enter__ and __exit__ on
  # XML-RPC.
  if sys.version_info.major == 2:
    yield server_proxy.supervisor
  else:
    with server_proxy as s:
      yield s.supervisor

def _getSupervisordSocketPath(instance_root, logger):
  legacy_socket_path = os.path.join(instance_root, 'supervisord.socket')
  socket_path = os.path.join(instance_root, 'sv.sock')
  if os.path.exists(legacy_socket_path):
    logger.info("Using legacy supervisor socket path %s", legacy_socket_path)

    # BBB slapos.core 1.6.1 had an issue that it started a new supervisord using
    # `socket_path`, while leaving the supervisord using `legacy_socket_path`
    # running with all processes attached.
    # When we deployed slapos.core 1.6.1 all servers had two supervisord processes:
    #     - legacy_socket_path with all processes running
    #     - socket_path with some processes in EXIT state because ports are already taken.
    # In this branch we clean up by stopping supervisord running on socket_path
    if os.path.exists(socket_path) and os.access(socket_path, os.R_OK):
      logger.critical(
          "We have two supervisord running ! "
          "Stopping the one using %s to keep using legacy %s instead",
          socket_path, legacy_socket_path)
      with getSupervisorRPC(socket_path) as supervisor:
        supervisor.stopAllProcesses()
        supervisor.shutdown()

    return legacy_socket_path

  return socket_path

def _getSupervisordConfigurationFilePath(instance_root):
  return os.path.join(instance_root, 'etc', 'supervisord.conf')

def _getSupervisordConfigurationDirectory(instance_root):
  return os.path.join(instance_root, 'etc', 'supervisord.conf.d')

def createSupervisordConfiguration(instance_root, logger, watchdog_command=''):
  """
  Create supervisord related files and directories.
  """
  if not os.path.isdir(instance_root):
    raise OSError('%s does not exist.' % instance_root)

  supervisord_configuration_file_path = _getSupervisordConfigurationFilePath(instance_root)
  supervisord_configuration_directory = _getSupervisordConfigurationDirectory(instance_root)
  supervisord_socket = _getSupervisordSocketPath(instance_root, logger)

  # Create directory accessible for the instances.
  var_directory = os.path.join(instance_root, 'var')
  if not os.path.isdir(var_directory):
    os.mkdir(var_directory)
  os.chmod(var_directory, stat.S_IRWXU | stat.S_IROTH | stat.S_IXOTH | \
                          stat.S_IRGRP | stat.S_IXGRP )
  etc_directory = os.path.join(instance_root, 'etc')
  if not os.path.isdir(etc_directory):
    os.mkdir(etc_directory)

  # Creates instance_root structure
  createPrivateDirectory(os.path.join(instance_root, 'var', 'log'))
  createPrivateDirectory(os.path.join(instance_root, 'var', 'run'))

  createPrivateDirectory(os.path.join(instance_root, 'etc'))
  createPrivateDirectory(supervisord_configuration_directory)

  # Creates supervisord configuration
  updateFile(supervisord_configuration_file_path,
    bytes2str(pkg_resources.resource_string(__name__,
      'templates/supervisord.conf.in')) % {
          'supervisord_configuration_directory': supervisord_configuration_directory,
          'supervisord_socket': os.path.abspath(supervisord_socket),
          'supervisord_loglevel': 'info',
          'supervisord_logfile': os.path.abspath(
              os.path.join(instance_root, 'var', 'log', 'supervisord.log')),
          'supervisord_logfile_maxbytes': '50MB',
          'supervisord_nodaemon': 'false',
          'supervisord_pidfile': os.path.abspath(
              os.path.join(instance_root, 'var', 'run', 'supervisord.pid')),
          'supervisord_logfile_backups': '10',
          # Do not set minfds. select() does not support file descriptors
          # greater than 1023.
          # 'supervisord_minfds': '4096',
          'watchdog_command': watchdog_command,
      }
  )

def _updateWatchdog(socket):
  """
  In special cases, supervisord can be started using configuration
  with empty watchdog parameter.
  Then, when running slapgrid, the real watchdog configuration is generated.
  We thus need to reload watchdog configuration if needed and start it.
  """
  with getSupervisorRPC(socket) as supervisor:
    if supervisor.getProcessInfo('watchdog')['state'] not in states.RUNNING_STATES:
      # XXX workaround for https://github.com/Supervisor/supervisor/issues/339
      # In theory, only reloadConfig is needed.
      supervisor.removeProcessGroup('watchdog')
      supervisor.reloadConfig()
      supervisor.addProcessGroup('watchdog')

def launchSupervisord(instance_root, logger,
                      supervisord_additional_argument_list=None):
  configuration_file = _getSupervisordConfigurationFilePath(instance_root)
  socket = _getSupervisordSocketPath(instance_root, logger)
  if os.path.exists(socket):
    trynum = 1
    while trynum < 6:
      try:
        with getSupervisorRPC(socket) as supervisor:
          status = supervisor.getState()
      except xmlrpclib.Fault as e:
        if e.faultCode == 6 and e.faultString == 'SHUTDOWN_STATE':
          logger.info('Supervisor in shutdown procedure, will check again later.')
          trynum += 1
          time.sleep(2 * trynum)
        else:
          raise
      except Exception:
        # In case if there is problem with connection, assume that supervisord
        # is not running and try to run it
        break
      else:
        if status['statename'] == 'RUNNING' and status['statecode'] == 1:
          logger.debug('Supervisord already running.')
          _updateWatchdog(socket)
          return
        elif status['statename'] == 'SHUTDOWN_STATE' and status['statecode'] == 6:
          logger.info('Supervisor in shutdown procedure, will check again later.')
          trynum += 1
          time.sleep(2 * trynum)
        else:
          log_message = 'Unknown supervisord state %r. Will try to start.' % status
          logger.warning(log_message)
          break

  supervisord_argument_list = ['-c', configuration_file]
  if supervisord_additional_argument_list is not None:
    supervisord_argument_list.extend(supervisord_additional_argument_list)

  logger.info("Launching supervisord with clean environment.")
  # Extract python binary to prevent shebang size limit
  invocation_list = [sys.executable, '-c']
  invocation_list.append(
      "import sys ; sys.path=" + str(sys.path) + " ; " +
      "import supervisor.supervisord ; " +
      "sys.argv[1:1]=" + str(supervisord_argument_list) + " ; " +
      "supervisor.supervisord.main()")
  supervisord_popen = SlapPopen(invocation_list,
                                env={},
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                logger=logger)

  result = supervisord_popen.output
  if supervisord_popen.returncode:
    logger.warning('Supervisord unknown problem: %s', result)
    raise RuntimeError('Failed to launch supervisord:\n%s' % result)

  try:
    default_timeout = socketlib.getdefaulttimeout()
    current_timeout = 1
    trynum = 1
    while trynum < 6:
      try:
        socketlib.setdefaulttimeout(current_timeout)
        with getSupervisorRPC(socket) as supervisor:
          status = supervisor.getState()
        if status['statename'] == 'RUNNING' and status['statecode'] == 1:
          return
        logger.warning('Wrong status name %(statename)r and code '
          '%(statecode)r, trying again' % status)
        trynum += 1
      except Exception:
        current_timeout = 5 * trynum
        trynum += 1
      else:
        logger.info('Supervisord started correctly in try %s.' % trynum)
        return
    logger.warning('Issue while checking supervisord.')
  finally:
    socketlib.setdefaulttimeout(default_timeout)

