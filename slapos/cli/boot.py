# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2010-2014 Vifib SARL and Contributors.
# All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsibility of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# guarantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public License
# as published by the Free Software Foundation; either version 2.1
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

from __future__ import print_function

import subprocess
from six.moves.urllib.parse import urlparse
from six.moves import xmlrpc_client as xmlrpclib
from time import sleep
import glob
import os
import netifaces
import socket
from netaddr import valid_ipv4, valid_ipv6
from slapos.cli.command import check_root_user
from slapos.cli.entry import SlapOSApp
from slapos.cli.config import ConfigCommand
from slapos.format import isGlobalScopeAddress
from slapos.grid.slapgrid import (COMPUTER_PARTITION_REQUESTED_STATE_FILENAME,
                                  COMPUTER_PARTITION_STARTED_STATE)
from slapos.grid.svcbackend import  (_getSupervisordSocketPath,
                                     getSupervisorRPC,
                                     launchSupervisord)
from slapos.util import string_to_boolean
import argparse
import logging

logger = logging.getLogger("slapos.boot")

def _removeTimestamp(instancehome, partition_base_name):
    """
    Remove .timestamp from all partitions
    """
    timestamp_glob_path = os.path.join(
        instancehome,
        "%s*" % partition_base_name,
        ".timestamp")
    for timestamp_path in glob.glob(timestamp_glob_path):
       logger.info("Removing %s", timestamp_path)
       os.remove(timestamp_path)

def _startComputerPartition(partition_id, supervisord_socket):
    """
    With supervisord, start the instance that was deployed
    """
    try:
      with getSupervisorRPC(supervisord_socket) as supervisor:
        supervisor.startProcessGroup(partition_id, False)
    except xmlrpclib.Fault as exc:
      if exc.faultString.startswith('BAD_NAME:'):
        logger.info("Nothing to start on %s...", partition_id)
      else:
        raise
    else:
      logger.info("Requested start of %s...", partition_id)

def _startComputerPartitionList(instance_root, partition_base_name):
  """
  Start services for partition which has requested state to 'started'
  """
  partition_glob_path = os.path.join(
        instance_root,
        "%s*" % partition_base_name)
  launchSupervisord(instance_root=instance_root, logger=logger)
  for partition_path in glob.glob(partition_glob_path):
    partition_state_path = os.path.join(
        partition_path,
        COMPUTER_PARTITION_REQUESTED_STATE_FILENAME
    )
    supervisord_socket_path = _getSupervisordSocketPath(
      instance_root,
      logger
    )
    if os.path.exists(partition_state_path):
      partition_state = ""
      with open(partition_state_path) as f:
        partition_state = f.read()
      if partition_state == COMPUTER_PARTITION_STARTED_STATE:
        # Call start for this computer partition
        _startComputerPartition(
          os.path.basename(partition_path.rstrip('/')),
          supervisord_socket_path
        )

def _runBang(app):
    """
    Launch slapos node format.
    """
    logger.info("[BOOT] Invoking slapos node bang...")
    result = app.run(['node', 'bang', '-m', 'Reboot'])
    if result == 1:
      return 0
    return 1


def _runFormat(app):
    """
    Launch slapos node format.
    """
    logger.info("[BOOT] Invoking slapos node format...")
    # '--local' parameter is to prevent node format command to post data to
    # master, so this command can work without internet and setup partitions IP.
    result = app.run(['node', 'format', '--now', '--local', '--verbose'])
    if result == 1:
      return 0
    return 1


def _ping(hostname):
    """
    Ping a hostname
    """
    logger.info("[BOOT] Invoking ipv4 ping to %s...", hostname)
    p = subprocess.Popen(["ping", "-c", "2", hostname],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    if p.returncode == 0:
      logger.info("[BOOT] IPv4 network reachable...")
      return 1
    logger.error("[BOOT] IPv4 network unreachable...")
    return 0


def _ping6(hostname):
    """
    Ping an ipv6 address
    """
    logger.info("[BOOT] Invoking ipv6 ping to %s...", hostname)
    p = subprocess.Popen(
        ["ping6", "-c", "2", hostname],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    if p.returncode == 0:
        logger.info("[BOOT] IPv6 network reachable...")
        return 1
    logger.error("[BOOT] IPv6 network unreachable...")
    return 0


def _test_ping(hostname):
  is_ready = _ping(hostname)
  while is_ready == 0:
    sleep(5)
    is_ready = _ping(hostname)


def _test_ping6(hostname):
  is_ready = _ping6(hostname)
  while is_ready == 0:
    sleep(5)
    is_ready = _ping6(hostname)


def _ping_hostname(hostname):
  is_ready = _ping6(hostname)
  while is_ready == 0:
    sleep(5)
    # Try ping on ipv4
    is_ready = _ping(hostname)
    if is_ready == 0:
      # try ping on ipv6
      is_ready = _ping6(hostname)


def _waitIpv6Ready(ipv6_interface):
  """
    test if ipv6 is ready on ipv6_interface
  """
  logger.info("[BOOT] Checking if %r has IPv6...", ipv6_interface)
  while True:
    for inet_dict in netifaces.ifaddresses(ipv6_interface).get(socket.AF_INET6, ()):
      ipv6_address = inet_dict['addr'].split('%')[0]
      if isGlobalScopeAddress(ipv6_address):
        return

    logger.error("[BOOT] No IPv6 found on interface %r, "
          "try again in 5 seconds...", ipv6_interface)
    sleep(5)

class BootCommand(ConfigCommand):
    """
    Test network and invoke simple format and bang (Use on Linux startup)
    """
    command_group = 'node'

    def get_parser(self, prog_name):
        ap = super(BootCommand, self).get_parser(prog_name)
        ap.add_argument('-m', '--message',
                        default="Reboot",
                        help='Message for bang')
        return ap

    def take_action(self, args):
        configp = self.fetch_config(args)
        instance_root = configp.get('slapos','instance_root')
        partition_base_name = "slappart"
        if configp.has_option('slapformat', 'partition_base_name'):
          partition_base_name = configp.get('slapformat', 'partition_base_name')
        master_url = urlparse(configp.get('slapos','master_url'))
        master_hostname = master_url.hostname

        root_check = True
        if configp.has_option('slapos', 'root_check'):
            root_check = configp.getboolean('slapos', 'root_check')

        if root_check:
            check_root_user(self)

        # Check that we have IPv6 ready
        if configp.has_option('slapformat', 'ipv6_interface'):
            ipv6_interface = configp.get('slapformat', 'ipv6_interface')
        elif configp.has_option('slapformat', 'interface_name'):
            ipv6_interface = configp.get('slapformat', 'interface_name')
        else:
            # It is most likely the we are running on unpriviledged environment
            # so we for slapformat handle it.
            ipv6_interface = None

        if ipv6_interface is not None:
            _waitIpv6Ready(ipv6_interface)

        app = SlapOSApp()
        # Make sure slapos node format returns ok
        while not _runFormat(app):
            logger.error("[BOOT] Fail to format, try again in 15 seconds...")
            sleep(15)

        # Start computer partition services
        _startComputerPartitionList(instance_root, partition_base_name)

        # Check that node can ping master
        if valid_ipv4(master_hostname):
            _test_ping(master_hostname)
        elif valid_ipv6(master_hostname):
            _test_ping6(master_hostname)
        else:
            # hostname
            _ping_hostname(master_hostname)

        # Make sure slapos node bang returns ok
        while not _runBang(app):
            logger.error("[BOOT] Fail to bang, try again in 15 seconds...")
            sleep(15)

        _removeTimestamp(instance_root, partition_base_name)
