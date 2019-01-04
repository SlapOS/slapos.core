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
from time import sleep
import glob
import os
import netifaces
import socket
from netaddr import valid_ipv4, valid_ipv6
from slapos.cli.command import must_be_root
from slapos.cli.entry import SlapOSApp
from slapos.cli.config import ConfigCommand
from slapos.format import isGlobalScopeAddress

def _removeTimestamp(instancehome):
    """
      Remove .timestamp from all partitions
    """
    timestamp_glob_path = "%s/slappart*/.timestamp" % instancehome
    for timestamp_path in glob.glob(timestamp_glob_path):
       print("Removing %s" % timestamp_path)
       os.remove(timestamp_path)

def _runBang(app):
    """
    Launch slapos node format.
    """
    print("[BOOT] Invoking slapos node bang...")
    result = app.run(['node', 'bang', '-m', 'Reboot'])
    if result == 1:
      return 0
    return 1

def _runFormat(app):
    """
    Launch slapos node format.
    """
    print("[BOOT] Invoking slapos node format...")
    result = app.run(['node', 'format', '--now', '--verbose'])
    if result == 1:
      return 0
    return 1

def _ping(hostname):
    """ 
    Ping a hostname
    """
    print("[BOOT] Invoking ipv4 ping to %s..." % hostname)
    p = subprocess.Popen(
      ["ping", "-c", "2", hostname],
       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    if p.returncode == 0:
      print("[BOOT] IPv4 network reachable...")
      return 1
    print("[BOOT] [ERROR] IPv4 network unreachable...")
    return 0

def _ping6(hostname):
    """ 
    Ping an ipv6 address
    """
    print("[BOOT] Invoking ipv6 ping to %s..." % hostname)
    p = subprocess.Popen(
        ["ping6", "-c", "2", hostname],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    if p.returncode == 0:
        print("[BOOT] IPv6 network reachable...")
        return 1
    print("[BOOT] [ERROR] IPv6 network unreachable...")
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
  ipv6_address = ""
  print("[BOOT] Checking if %r has IPv6..." % ipv6_interface)
  while ipv6_address == "":
    for inet_dict in netifaces.ifaddresses(ipv6_interface)[socket.AF_INET6]:
      ipv6_address = inet_dict['addr'].split('%')[0]
      if isGlobalScopeAddress(ipv6_address):
        break
    else:
      ipv6_address = ""
      print("[BOOT] [ERROR] No IPv6 found on interface %r, "
        "try again in 5 seconds..." % ipv6_interface)
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

    @must_be_root
    def take_action(self, args):
        configp = self.fetch_config(args)
        instance_root = configp.get('slapos','instance_root')
        master_url = urlparse(configp.get('slapos','master_url'))
        master_hostname = master_url.hostname

        # Check that we have IPv6 ready
        if configp.has_option('slapformat', 'ipv6_interface'):
            ipv6_interface = configp.get('slapformat', 'ipv6_interface')
        else:
            ipv6_interface = configp.get('slapformat', 'interface_name')
        _waitIpv6Ready(ipv6_interface)

        # Check that node can ping master
        if valid_ipv4(master_hostname):
          _test_ping(master_hostname)
        elif valid_ipv6(master_hostname):
          _test_ping6(master_hostname)
        else:
          # hostname
          _ping_hostname(master_hostname)

        app = SlapOSApp()
        # Make sure slapos node format returns ok
        while not _runFormat(app):
            print("[BOOT] [ERROR] Fail to format, try again in 15 seconds...")
            sleep(15)
       
        # Make sure slapos node bang returns ok
        while not _runBang(app):
            print("[BOOT] [ERROR] Fail to bang, try again in 15 seconds...")
            sleep(15)

        _removeTimestamp(instance_root)
