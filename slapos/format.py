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

from six.moves import configparser
import distro
import enum
import errno
import fcntl
import grp
import json
import logging
import math
import netaddr
import netifaces
import os
import glob
import pwd
import random
import shutil
import socket
import struct
import subprocess
import sys
import threading
import time
import traceback
import zipfile
import platform
from six.moves.urllib.request import urlopen
import six

import lxml.etree
import xml_marshaller.xml_marshaller

from slapos.util import (dumps, mkdir_p, ipv6FromBin, binFromIpv6,
                        lenNetmaskIpv6, getPartitionIpv6Addr,
                        getPartitionIpv6Range, getTapIpv6Range,
                        getTunIpv6Range, netmaskFromLenIPv6,
                        getIpv6RangeFirstAddr)
import slapos.slap as slap
from slapos import version
from slapos import manager as slapmanager


class FormatReturn(enum.IntEnum):
  SUCCESS = 0
  FAILURE = 1
  OFFLINE_SUCCESS = 2


logger = logging.getLogger("slapos.format")


def prettify_xml(xml):
  root = lxml.etree.fromstring(xml)
  return lxml.etree.tostring(root, pretty_print=True)


class OS(object):
  """Wrap parts of the 'os' module to provide logging of performed actions."""

  _os = os

  def __init__(self, conf):
    self._dry_run = conf.dry_run
    self._logger = conf.logger
    add = self._addWrapper
    add('chown')
    add('chmod')
    add('makedirs')
    add('mkdir')

  def _addWrapper(self, name):
    def wrapper(*args, **kw):
      arg_list = [repr(x) for x in args] + [
          '%s=%r' % (x, y) for x, y in six.iteritems(kw)
      ]
      self._logger.debug('%s(%s)' % (name, ', '.join(arg_list)))
      if not self._dry_run:
        getattr(self._os, name)(*args, **kw)
    setattr(self, name, wrapper)

  def __getattr__(self, name):
    return getattr(self._os, name)


class UsageError(Exception):
  pass


class NoAddressOnInterface(Exception):
  """
  Exception raised if there is no address on the interface to construct IPv6
  address with.

  Attributes:
    brige: String, the name of the interface.
  """

  def __init__(self, interface):
    super(NoAddressOnInterface, self).__init__(
      'No IPv6 found on interface %s to construct IPv6 with.' % interface
    )


class AddressGenerationError(Exception):
  """
  Exception raised if the generation of an IPv6 based on the prefix obtained
  from the interface failed.

  Attributes:
    addr: String, the invalid address the exception is raised for.
  """
  def __init__(self, addr):
    super(AddressGenerationError, self).__init__(
      'Generated IPv6 %s seems not to be a valid IP.' % addr
    )


def getNormalizedIfaddresses(iface, inet):
  """
  Keep a single representation for netmasks, to avoid netmasks like
  ffff:ffff:ffff:ffff:ffff:ffff::/96
  """
  address_list = netifaces.ifaddresses(iface)[inet]
  for q in address_list:
    try:
      q['netmask'] = q['netmask'].split('/')[0]
    except KeyError:
      pass
  return address_list

def getPublicIPv4Address():
  test_list = [
    { "url": 'https://api.ipify.org/?format=json' , "json_key": "ip"},
    { "url": 'http://httpbin.org/ip', "json_key": "origin"},
    { "url": 'http://jsonip.com', "json_key": "ip"}]
  previous = None
  ipv4 = None
  for test in test_list:
    if ipv4 is not None:
      previous = ipv4
    try:
      ipv4 = json.load(urlopen(test["url"], timeout=15))[test["json_key"]]
    except:
      ipv4 = None
    if ipv4 is not None and ipv4 == previous:
      return ipv4

def callAndRead(argument_list, raise_on_error=True):
  popen = subprocess.Popen(
    argument_list,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    universal_newlines=True,
  )
  result = popen.communicate()[0]
  if raise_on_error and popen.returncode != 0:
    raise ValueError('Issue while invoking %r, result was:\n%s' % (
                     argument_list, result))
  return popen.returncode, result


def isGlobalScopeAddress(a):
  """Returns True if a is global scope IP v4/6 address"""
  ip = netaddr.IPAddress(a)
  return not ip.is_link_local() and not ip.is_loopback() and \
      not ip.is_reserved() and ip.is_unicast()


def netmaskToPrefixIPv4(netmask):
  """Convert string represented netmask to its integer prefix"""
  return netaddr.strategy.ipv4.netmask_to_prefix[
          netaddr.strategy.ipv4.str_to_int(netmask)]

def getIfaceAddressIPv4(iface):
  """return dict containing ipv4 address netmask, network and broadcast address
  of interface"""
  if not iface in netifaces.interfaces():
    raise ValueError('Could not find interface called %s to use as gateway ' \
                      'for tap network' % iface)
  try:
    addresses_list = getNormalizedIfaddresses(iface, socket.AF_INET)
    if len (addresses_list) > 0:

      addresses = addresses_list[0].copy()
      addresses['network'] = str(netaddr.IPNetwork('%s/%s' % (addresses['addr'],
                                          addresses['netmask'])).cidr.network)
      return addresses
    else:
      return {}
  except KeyError:
    raise KeyError('Could not find IPv4 adress on interface %s.' % iface)

def getIPv4SubnetAddressRange(ip_address, mask, size):
  """Check if a given ipaddress can be used to create 'size'
  host ip address, then return list of ip address in the subnet"""
  ip = netaddr.IPNetwork('%s/%s' % (ip_address, mask))
  # Delete network and default ip_address from the list
  ip_list = [x for x in sorted(list(ip))
              if str(x) != ip_address and x.value != ip.cidr.network.value]
  if len(ip_list) < size:
    raise ValueError('Could not create %s tap interfaces from address %s.' % (
              size, ip_address))
  return ip_list

def _getDict(obj):
  """
  Serialize an object into dictionaries. List and dict will remains
  the same, basic type too. But encapsulated object will be returned as dict.
  Set, collections and other aren't handle for now.

  Args:
    obj: an object of any type.

  Returns:
    A dictionary if the given object wasn't a list, a list otherwise.
  """
  if isinstance(obj, list):
    return [_getDict(item) for item in obj]

  if isinstance(obj, dict):
    dikt = obj
  else:
    try:
      dikt = obj.__dict__
    except AttributeError:
      return obj

  return {
    key: _getDict(value)
    for key, value in six.iteritems(dikt)
    # do not attempt to serialize logger: it is both useless and recursive.
    # do not serialize attributes starting with "_", let the classes have some privacy
    if not key.startswith("_")
  }


class Computer(object):
  """Object representing the computer"""

  def __init__(self, reference, interface=None, addr=None, netmask=None,
               ipv6_interface=None, partition_has_ipv6_range=None, software_user='slapsoft',
               tap_gateway_interface=None, tap_ipv6=None,
               instance_root=None, software_root=None, instance_storage_home=None,
               partition_list=None, config=None):
    """
    Attributes:
      reference: str, the reference of the computer.
      interface: str, the name of the computer's used interface.

      :param config: dict-like, holds raw data from configuration file
    """
    self.reference = str(reference)
    self.interface = interface
    self.partition_list = partition_list or []
    self.address = addr
    # Normalize netmask due to netiface netmasks like ffff::/16
    self.netmask = netmask and netmask.split('/')[0]
    self.ipv6_interface = ipv6_interface
    self.partition_has_ipv6_range = partition_has_ipv6_range
    self.software_user = software_user
    self.tap_gateway_interface = tap_gateway_interface
    self.tap_ipv6 = tap_ipv6

    # Used to be static attributes of the class object - didn't make sense (Marco again)
    assert instance_root is not None and software_root is not None, \
           "Computer's instance_root and software_root must not be empty!"
    self.software_root = software_root
    self.instance_root = instance_root
    self.instance_storage_home = instance_storage_home

    # The following properties are updated on update() method
    self.public_ipv4_address = None
    self.os_type = None
    self.python_version = None
    self.slapos_version = None

    # attributes starting with '_' are saved from serialization
    # monkey-patch use of class instead of dictionary
    if config is None:
      logger.warning("Computer needs config in constructor to allow managers.")

    self._config = config if config is None or isinstance(config, dict) else config.__dict__
    self._manager_list = slapmanager.from_config(self._config)

  def __getinitargs__(self):
    return (self.reference, self.interface)

  def getAddress(self):
    """
    Return a list of the interface address not attributed to any partition (which
    are therefore free for the computer itself).

    Returns:
      False if the interface isn't available, else the list of the free addresses.
    """
    if self.interface is None:
      return {'addr': self.address, 'netmask': self.netmask}

    computer_partition_address_list = []
    for partition in self.partition_list:
      for address in partition.address_list:
        if netaddr.valid_ipv6(address['addr']):
          computer_partition_address_list.append(address['addr'])
    # Going through addresses of the computer's interface
    available_address_list = self.interface.getGlobalScopeAddressList()
    # First scan: prefer the existing address, as the available_address_list
    #             might be sorted differently
    for address_dict in available_address_list:
      if self.address == address_dict['addr']:
        if self.address not in computer_partition_address_list:
          return address_dict

    # Second scan: take first not occupied address
    for address_dict in available_address_list:
      # Comparing with computer's partition addresses
      if address_dict['addr'] not in computer_partition_address_list:
        return address_dict

    # Can't find address
    raise NoAddressOnInterface('No valid IPv6 found on %s.' % self.interface.name)

  def update(self):
    """Collect environmental hardware/network information."""
    self.public_ipv4_address = getPublicIPv4Address()
    self.slapos_version = version.version
    self.python_version = platform.python_version()
    self.os_type = json.dumps((platform.platform(),distro.id(),distro.version(),distro.name()))

  def send(self, conf):
    """
    Send a marshalled dictionary of the computer object serialized via_getDict.
    """
    slap_instance = slap.slap()
    connection_dict = {}
    if conf.key_file and conf.cert_file:
      connection_dict['key_file'] = conf.key_file
      connection_dict['cert_file'] = conf.cert_file
    slap_instance.initializeConnection(conf.master_url,
                                       **connection_dict)
    slap_computer = slap_instance.registerComputer(self.reference)

    if conf.dry_run:
      return
    try:
      slap_computer.updateConfiguration(dumps(_getDict(self)))
    except slap.NotFoundError as error:
      raise slap.NotFoundError("%s\nERROR: This SlapOS node is not recognised by "
          "SlapOS Master and/or computer_id and certificates don't match. "
          "Please make sure computer_id of slapos.cfg looks "
          "like 'COMP-123' and is correct.\nError is : 404 Not Found." % error)

  def dump(self, path_to_xml, path_to_json, logger):
    """
    Dump the computer object to an xml file via xml_marshaller.

    Args:
      path_to_xml: String, path to the file to load.
      path_to_json: String, path to the JSON version to save.
    """

    # dump partition resources information
    for partition in self.partition_list:
      partition.dump()

    computer_dict = _getDict(self)

    if path_to_json:
      with open(path_to_json, 'w') as fout:
        json.dump(computer_dict, fout, sort_keys=True, indent=2)

    new_xml = dumps(computer_dict)
    new_pretty_xml = prettify_xml(new_xml)

    path_to_archive = path_to_xml + '.zip'

    if os.path.exists(path_to_archive) and os.path.exists(path_to_xml):
      # the archive file exists, we only backup if something has changed
      with open(path_to_xml, 'rb') as fin:
        if fin.read() == new_pretty_xml:
          # computer configuration did not change, nothing to write
          return

    if os.path.exists(path_to_xml):
      try:
        self.backup_xml(path_to_archive, path_to_xml)
      except:
        # might be a corrupted zip file. let's move it out of the way and retry.
        shutil.move(path_to_archive,
                    path_to_archive + time.strftime('_broken_%Y%m%d-%H:%M'))
        try:
          self.backup_xml(path_to_archive, path_to_xml)
        except:
          # give up trying
          logger.exception("Can't backup %s:", path_to_xml)

    with open(path_to_xml, 'wb') as fout:
      fout.write(new_pretty_xml)

  def backup_xml(self, path_to_archive, path_to_xml):
    """
    Stores a copy of the current xml file to an historical archive.
    """
    xml_content = open(path_to_xml).read()
    saved_filename = os.path.basename(path_to_xml) + time.strftime('.%Y%m%d-%H:%M')

    with zipfile.ZipFile(path_to_archive, 'a') as archive:
      archive.writestr(saved_filename, xml_content, zipfile.ZIP_DEFLATED)

  @classmethod
  def load(cls, path_to_xml, reference, ipv6_interface, partition_has_ipv6_range, tap_gateway_interface,
           tap_ipv6, instance_root=None, software_root=None, config=None):
    """
    Create a computer object from a valid xml file.

    Arg:
      path_to_xml: String, a path to a valid file containing
          a valid configuration.

    Return:
      A Computer object.
    """
    with open(path_to_xml, "rb") as fi:
      dumped_dict = xml_marshaller.xml_marshaller.load(fi)

    # Reconstructing the computer object from the xml
    computer = Computer(
        reference=reference,
        addr=dumped_dict['address'],
        netmask=dumped_dict['netmask'],
        ipv6_interface=ipv6_interface,
        partition_has_ipv6_range=partition_has_ipv6_range,
        software_user=dumped_dict.get('software_user', 'slapsoft'),
        tap_gateway_interface=tap_gateway_interface,
        tap_ipv6=tap_ipv6,
        software_root=dumped_dict.get('software_root', software_root),
        instance_root=dumped_dict.get('instance_root', instance_root),
        config=config,
    )

    partition_amount = int(config.partition_amount)
    for partition_index, partition_dict in enumerate(dumped_dict['partition_list']):

      if partition_dict['user']:
        user = User(partition_dict['user']['name'])
      else:
        user = User('root')

      if partition_dict['tap']:
        tap = Tap(partition_dict['tap']['name'])
        tap.ipv4_addr = partition_dict['tap'].get('ipv4_addr', '')
        tap.ipv4_netmask = partition_dict['tap'].get('ipv4_netmask', '')
        tap.ipv4_gateway = partition_dict['tap'].get('ipv4_gateway', '')
        tap.ipv4_network = partition_dict['tap'].get('ipv4_network', '')
        tap.ipv6_addr = partition_dict['tap'].get('ipv6_addr', '')
        tap.ipv6_netmask = partition_dict['tap'].get('ipv6_netmask', '')
        tap.ipv6_gateway = partition_dict['tap'].get('ipv6_gateway', '')
        tap.ipv6_network = partition_dict['tap'].get('ipv6_network', '')
      else:
        tap = Tap(partition_dict['reference'])

      tun_dict = partition_dict.get('tun')
      if tun_dict is None:
        if config.create_tun:
          tun = Tun("slaptun" + str(partition_index), partition_index, partition_amount, config.tun_ipv6)
        else:
          tun = None
      else:
        ipv4_addr = tun_dict.get('ipv4_addr')
        ipv6_addr = tun_dict.get('ipv6_addr')
        needs_ipv6 = not ipv6_addr and config.tun_ipv6
        tun = Tun(tun_dict['name'], partition_index, partition_amount, needs_ipv6)
        if ipv4_addr:
          tun.ipv4_addr = ipv4_addr
          tun.ipv4_netmask = tun_dict['ipv4_netmask']
          tun.ipv4_network = tun_dict['ipv4_network']
        if ipv6_addr:
          tun.ipv6_addr = ipv6_addr
          tun.ipv6_netmask = tun_dict['ipv6_netmask']
          tun.ipv6_network = tun_dict['ipv6_network']

      address_list = partition_dict['address_list']
      ipv6_range = partition_dict.get('ipv6_range', {})
      external_storage_list = partition_dict.get('external_storage_list', [])

      partition = Partition(
          reference=partition_dict['reference'],
          path=partition_dict['path'],
          user=user,
          address_list=address_list,
          ipv6_range=ipv6_range,
          tap=tap,
          tun=tun,
          external_storage_list=external_storage_list,
      )

      computer.partition_list.append(partition)

    return computer

  def _speedHackAddAllOldIpsToInterface(self):
    """
    Speed hack:
    Blindly add all IPs from existing configuration, just to speed up actual
    computer configuration later on.
    """
    # XXX-TODO: only add an address if it doesn't already exist.
    if self.ipv6_interface:
      interface_name = self.ipv6_interface
    elif self.interface:
      interface_name = self.interface.name
    else:
      return

    for partition in self.partition_list:
      try:
        for address in partition.address_list:
          try:
            netmask = lenNetmaskIpv6(address['netmask'])
          except:
            continue
          callAndRead(['ip', 'addr', 'add',
                       '%s/%s' % (address['addr'], netmask),
                       'dev', interface_name])
      except ValueError:
        pass

  @property
  def software_gid(self):
    """Return GID for self.software_user.

    Has to be dynamic because __init__ happens before ``format`` where we
    effectively create the user and group."""
    return pwd.getpwnam(self.software_user)[3]

  def format(self, alter_user=True, alter_network=True, create_tap=True):
    """
    Setup underlaying OS so it reflects this instance (``self``).

    - setup interfaces and addresses
    - setup TAP and TUN interfaces
    - add groups and users
    - construct partitions inside slapgrid
    """
    for path in self.instance_root, self.software_root:
      if not os.path.exists(path):
        os.makedirs(path, 0o755)
      else:
        os.chmod(path, 0o755)

    # own self.software_root by software user
    slapsoft = User(self.software_user)
    slapsoft.path = self.software_root
    if alter_user:
      slapsoft.create()
      slapsoft_pw = pwd.getpwnam(slapsoft.name)
      os.chown(slapsoft.path, slapsoft_pw.pw_uid, slapsoft_pw.pw_gid)
    os.chmod(self.software_root, 0o755)

    # Iterate over all managers and let them `format` the computer too
    for manager in self._manager_list:
      manager.format(self)

    # get list of instance external storage if exist
    instance_external_list = []
    if self.instance_storage_home:
      # get all /XXX/dataN where N is a digit
      data_list = glob.glob(os.path.join(self.instance_storage_home, 'data*'))
      for i in range(0, len(data_list)):
        data_path = data_list.pop()
        the_digit = os.path.basename(data_path).split('data')[-1]
        if the_digit.isdigit():
          instance_external_list.append(data_path)

    ####################
    ### Network part ###
    ####################
    if alter_network:
      if self.address is not None:
        self.interface.addIPv6Address(
          partition_index=None,
          addr=self.address,
          netmask=self.netmask
        )

      if create_tap and self.tap_gateway_interface:
        gateway_addr_dict = getIfaceAddressIPv4(self.tap_gateway_interface)
        tap_address_list = getIPv4SubnetAddressRange(gateway_addr_dict['addr'],
                              gateway_addr_dict['netmask'],
                              len(self.partition_list))
        assert(len(self.partition_list) <= len(tap_address_list))

      if self.partition_has_ipv6_range:
        self.interface.allowNonlocalBind()

      self._speedHackAddAllOldIpsToInterface()

    try:
      for partition_index, partition in enumerate(self.partition_list):
        # Reconstructing User's
        partition.path = os.path.join(self.instance_root, partition.reference)
        partition.user.setPath(partition.path)
        partition.user.additional_group_list = [slapsoft.name]
        partition.external_storage_list = ['%s/%s' % (path, partition.reference)
                                            for path in instance_external_list]
        if alter_user:
          partition.user.create()

        # Reconstructing Tap and Tun
        if alter_network:
          if partition.user and partition.user.isAvailable():
            owner = partition.user
          else:
            owner = User('root')

          if create_tap:
            partition.tap.createWithOwner(owner)

            if self.tap_gateway_interface:
              # add addresses and create route for this tap
              # Pop IP from tap_address_list and attach to tap if has no ipv4 yet
              next_ipv4_addr = '%s' % tap_address_list.pop(0)
              # skip to set this IP to tap if already exits
              if not partition.tap.ipv4_addr:
                # define new ipv4 address for this tap
                partition.tap.ipv4_addr = next_ipv4_addr
                partition.tap.ipv4_netmask = gateway_addr_dict['netmask']
                partition.tap.ipv4_gateway = gateway_addr_dict['addr']
                partition.tap.ipv4_network = gateway_addr_dict['network']
            else:
              partition.tap.ipv4_addr = ''
              partition.tap.ipv4_netmask = ''
              partition.tap.ipv4_gateway = ''
              partition.tap.ipv4_network = ''

            if self.tap_ipv6:
              if not partition.tap.ipv6_addr:
                # create a new IPv6 randomly for the tap
                ipv6_dict = self.interface.addIPv6Address(partition_index, tap=partition.tap)
                partition.tap.ipv6_addr = ipv6_dict['addr']
                partition.tap.ipv6_netmask = ipv6_dict['netmask']
              else:
                # make sure the tap has its IPv6
                self.interface.addIPv6Address(
                        partition_index=partition_index,
                        addr=partition.tap.ipv6_addr,
                        netmask=partition.tap.ipv6_netmask,
                        tap=partition.tap)

              # construct ipv6_network (16 bit more than the computer network)
              prefixlen = lenNetmaskIpv6(self.interface.getGlobalScopeAddressList()[0]['netmask']) + 16
              gateway_addr = getIpv6RangeFirstAddr(partition.tap.ipv6_addr, prefixlen)
              partition.tap.ipv6_gateway = gateway_addr
              partition.tap.ipv6_network = "{}/{}".format(gateway_addr, prefixlen)
            else:
              partition.tap.ipv6_addr = ''
              partition.tap.ipv6_netmask = ''
              partition.tap.ipv6_gateway = ''
              partition.tap.ipv6_network = ''

            # create IPv4 and IPv6 routes
            partition.tap.createRoutes()

          if partition.tun is not None:
            # create TUN interface per partition as well
            partition.tun.createWithOwner(owner)
            if partition.tun._needs_ipv6:
              ipv6_dict = self.interface.generateIPv6Range(partition_index, tun=True)
              prefixlen = ipv6_dict['prefixlen']
              ipv6_addr = getIpv6RangeFirstAddr(ipv6_dict['addr'], prefixlen)
              partition.tun.ipv6_addr = ipv6_addr
              partition.tun.ipv6_netmask = ipv6_dict['netmask']
              partition.tun.ipv6_network = "%s/%d" % (ipv6_addr, prefixlen)
            partition.tun.createRoutes()

          # Reconstructing partition's address
          # There should be two addresses on each Computer Partition:
          #  * local IPv4, took from slapformat:ipv4_local_network
          #  * global IPv6
          if not partition.address_list:
            # generate new addresses
            partition.address_list.append(self.interface.addIPv4LocalAddress())
            partition_ipv6_dict = self.interface.addIPv6Address(partition_index)
            # Avoid leaking prefixlen in dumped data because it is not loaded
            # otherwise format dumps a different result after the first run
            partition_ipv6_dict.pop('prefixlen', None)
            partition.address_list.append(partition_ipv6_dict)
          else:
            # regenerate list of addresses
            old_partition_address_list = partition.address_list
            partition.address_list = []
            if len(old_partition_address_list) != 2:
              raise ValueError(
                'There should be exactly 2 stored addresses. Got: %r' %
                (old_partition_address_list,))
            if not any(netaddr.valid_ipv6(q['addr'])
                       for q in old_partition_address_list):
              raise ValueError('No valid IPv6 address loaded from XML config')
            if not any(netaddr.valid_ipv4(q['addr'])
                       for q in old_partition_address_list):
              raise ValueError('No valid IPv4 address loaded from XML config')

            for address in old_partition_address_list:
              if netaddr.valid_ipv6(address['addr']):
                partition.address_list.append(self.interface.addIPv6Address(
                  partition_index,
                  address['addr'],
                  address['netmask']))
              elif netaddr.valid_ipv4(address['addr']):
                partition.address_list.append(self.interface.addIPv4LocalAddress(
                  address['addr']))
              else:
                # should never happen since there are exactly 1 valid IPv6 and 1
                # valid IPv4 in old_partition_address_list
                raise ValueError('Address %r is incorrect' % address['addr'])

          # Reconstructing partition's IPv6 range
          if self.partition_has_ipv6_range:
            if not partition.ipv6_range:
              # generate new IPv6 range
              partition.ipv6_range = self.interface.generateIPv6Range(partition_index)
            else:
              if not netaddr.valid_ipv6(partition.ipv6_range['addr']):
                raise ValueError('existing IPv6 range %r is incorrect', partition.ipv6_range['addr'])
            self.interface.addLocalRouteIpv6Range(partition.ipv6_range)
          else:
            partition.ipv6_range = {}

        # Reconstructing partition's directory
        partition.createPath(alter_user)
        partition.createExternalPath(alter_user)

    finally:
      for manager in self._manager_list:
        manager.formatTearDown(self)


class Partition(object):
  """Represent a computer partition."""

  resource_file = ".slapos-resource"

  def __init__(self, reference, path, user, address_list,
               ipv6_range, tap, tun=None, external_storage_list=[]):
    """
    Attributes:
      reference: String, the name of the partition.
      path: String, the path to the partition folder.
      user: User, the user linked to this partition.
      address_list: List of associated IP addresses.
      ipv6_range: IPv6 range given to this partition (dict with 'addr' and 'netmask').
      tap: Tap, the tap interface linked to this partition e.g. used as a gateway for kvm
      tun: Tun interface used for special apps simulating ethernet connections
      external_storage_list: Base path list of folder to format for data storage
    """

    self.reference = str(reference)
    self.path = str(path)
    self.user = user
    self.address_list = address_list or []
    self.ipv6_range = ipv6_range or {}
    self.tap = tap
    self.tun = tun
    self.external_storage_list = []

  def __getinitargs__(self):
    return (self.reference, self.path, self.user, self.address_list, self.ipv6_range, self.tap, self.tun)

  def createPath(self, alter_user=True):
    """
    Create the directory of the partition, assign to the partition user and
    give it the 750 permission. In case if path exists just modifies it.
    """

    self.path = os.path.abspath(self.path)
    owner = self.user if self.user else User('root')
    if not os.path.exists(self.path):
      os.mkdir(self.path, 0o750)
    if alter_user:
      owner_pw = pwd.getpwnam(owner.name)
      os.chown(self.path, owner_pw.pw_uid, owner_pw.pw_gid)
    os.chmod(self.path, 0o750)

  def createExternalPath(self, alter_user=True):
    """
    Create and external directory of the partition, assign to the partition user
    and give it the 750 permission. In case if path exists just modifies it.
    """

    for path in self.external_storage_list:
      storage_path = os.path.abspath(path)
      owner = self.user if self.user else User('root')
      if not os.path.exists(storage_path):
        os.mkdir(storage_path, 0o750)
      if alter_user:
        owner_pw = pwd.getpwnam(owner.name)
        os.chown(storage_path, owner_pw.pw_uid, owner_pw.pw_gid)
      os.chmod(storage_path, 0o750)

  def dump(self):
    """Dump available resources into ~partition_home/.slapos-resource."""
    file_path = os.path.join(self.path, self.resource_file)
    data = _getDict(self)
    content = json.dumps(data, sort_keys=True, indent=4)
    if os.path.exists(file_path):
      with open(file_path, "r") as f:
        if f.read() == content:
          # dumped resources didn't change
          return

    with open(file_path, "w") as fo:
      fo.write(content)
    owner_pw = pwd.getpwnam(self.user.name)
    os.chmod(file_path, 0o644)
    logger.info("Partition resources saved to {}".format(
      self.reference, file_path))


class User(object):
  """User: represent and manipulate a user on the system."""

  path = None

  def __init__(self, user_name, additional_group_list=None):
    """
    Attributes:
        user_name: string, the name of the user, who will have is home in
    """
    self.name = str(user_name)
    self.shell = '/bin/sh'
    self.additional_group_list = additional_group_list

  def __getinitargs__(self):
    return (self.name,)

  def setPath(self, path):
    self.path = path

  def create(self):
    """
    Create a user on the system who will be named after the self.name with its
    own group and directory.

    Returns:
        True: if the user creation went right
    """
    # XXX: This method shall be no-op in case if all is correctly setup
    #      This method shall check if all is correctly done
    grpname = 'grp_' + self.name if sys.platform == 'cygwin' else self.name
    try:
      grp.getgrnam(grpname)
    except KeyError:
      callAndRead(['groupadd', grpname])

    user_parameter_list = ['-d', self.path, '-g', self.name, '-s', self.shell]
    additional_groups_flag = '-aG'
    command = 'usermod'

    try:
      pwd.getpwnam(self.name)
    except KeyError:
      user_parameter_list.append('-r')
      additional_groups_flag = '-G'
      command = 'useradd'

    if self.additional_group_list is not None:
      user_parameter_list.extend([additional_groups_flag, ','.join(self.additional_group_list)])

    user_parameter_list.insert(0, command)
    user_parameter_list.append(self.name)

    callAndRead(user_parameter_list, raise_on_error=False)
    # lock the password of user
    callAndRead(['passwd', '-l', self.name])

    return True

  def isAvailable(self):
    """
    Determine the availability of a user on the system

    Return:
        True: if available
        False: otherwise
    """

    try:
      pwd.getpwnam(self.name)
      return True
    except KeyError:
      return False


class Tap(object):
  "Tap represent a tap interface on the system"
  IFF_TAP = 0x0002
  TUNSETIFF = 0x400454ca
  KEEP_TAP_ATTACHED_EVENT = threading.Event()
  MODE = "tap"

  def __init__(self, tap_name):
    """
    Attributes:
        tap_name: String, the name of the tap interface.
        ipv4_address: String, local ipv4 to route to this tap
        ipv4_network: String, netmask to use when configure route for this tap
        ipv4_gateway: String, ipv4 of gateway to be used to reach local network
    """

    self.name = str(tap_name)
    self.ipv4_addr = ""
    self.ipv4_netmask = ""
    self.ipv4_gateway = ""
    self.ipv4_network = ""
    self.ipv6_addr = ""
    self.ipv6_netmask = ""
    self.ipv6_gateway = ""
    self.ipv6_network = ""


  def __getinitargs__(self):
    return (self.name,)

  def createWithOwner(self, owner):
    """
    Create a tap interface on the system if it doesn't exist yet.
    """
    check_file = '/sys/devices/virtual/net/%s/owner' % self.name
    owner_id = None
    if os.path.exists(check_file):
      with open(check_file) as fx:
        owner_id = fx.read().strip()
      try:
        owner_id = int(owner_id)
      except ValueError:
        owner_id = pwd.getpwnam(owner_id).pw_uid
      #
      if owner_id != pwd.getpwnam(owner.name).pw_uid:
        logger.warning("Wrong owner of TUN/TAP interface {}! Not touching it."
                       "Expected {:d} got {:d}".format(
          self.name, pwd.getpwnam(owner.name).pw_uid, owner_id))
      # if the interface already exists - don't do anything
      return

    callAndRead(['ip', 'tuntap', 'add', 'dev', self.name, 'mode',
                 self.MODE, 'user', owner.name])
    callAndRead(['ip', 'link', 'set', self.name, 'up'])

  def createRoutes(self):
    """
    Configure ipv4 and ipv6 routes
    """
    if self.ipv4_addr:
      # Check if this route exits
      code, result = callAndRead(['ip', 'route', 'show', self.ipv4_addr],
                                 raise_on_error=False)
      if code != 0 or self.ipv4_addr not in result or self.name not in result:
        callAndRead(['ip', 'route', 'add', self.ipv4_addr, 'dev', self.name])

    if self.ipv6_network:
      # Check if this route exits
      code, result = callAndRead(['ip', '-6', 'route', 'show', self.ipv6_gateway],
                                 raise_on_error=False)
      if code != 0 or self.name not in result:
        callAndRead(['ip', '-6', 'route', 'add', self.ipv6_gateway, 'dev', self.name])

      code, result = callAndRead(['ip', '-6', 'route', 'show', self.ipv6_network],
                                 raise_on_error=False)
      if code != 0 or 'via {}'.format(self.ipv6_gateway) not in result or 'dev {}'.format(self.name) not in result:
        if 'dev {}'.format(self.name) in result:
          callAndRead(['ip', '-6', 'route', 'del', self.ipv6_network, 'dev', self.name]) # remove old route without the "via" option
        callAndRead(['ip', '-6', 'route', 'add', self.ipv6_network, 'dev', self.name, 'via', self.ipv6_gateway])



class Tun(Tap):
  """Represent TUN interface which might be many per user."""

  MODE = "tun"
  BASE_MASK = 12
  BASE_NETWORK = "172.16.0.0"

  def __init__(self, name, sequence=None, partitions=None, needs_ipv6=False):
    """Create TUN interface with subnet according to the optional ``sequence`` number.

    :param name: name which will appear in ``ip list`` afterwards
    :param sequence: {int} position of this TUN among all ``partitions``
    """
    super(Tun, self).__init__(name)
    self._needs_ipv6 = needs_ipv6
    if sequence is not None:
      assert 0 <= sequence < partitions, "0 <= {} < {}".format(sequence, partitions)
      # create base IPNetwork
      ip_network = netaddr.IPNetwork(Tun.BASE_NETWORK + "/" + str(Tun.BASE_MASK))
      # compute shift in BITS to separate ``partitions`` networks into subset
      # example: for 30 partitions we need log2(30) = 8 BITS
      mask_shift = int(math.ceil(math.log(int(partitions), 2.0)))
      # IPNetwork.subnet returns iterator over all possible subnets of given mask
      ip_subnets = list(ip_network.subnet(Tun.BASE_MASK + mask_shift))
      subnet = ip_subnets[sequence]
      # For serialization purposes, convert directly to ``str``
      self.ipv4_network = "{}/{}".format(subnet[1], subnet.netmask)
      self.ipv4_addr = str(subnet[1])
      self.ipv4_netmask = str(subnet.netmask)

  def createRoutes(self):
    """Extend for physical addition of network address because TAP let this on external class."""
    if self.ipv4_network:
      # add an address
      code, _ = callAndRead(
        ['ip', 'addr', 'add', self.ipv4_network, 'dev', self.name],
        raise_on_error=False)
      if code == 0:
        # address added to the interface - wait
        time.sleep(1)
    if self.ipv6_network:
      # add an address
      code, _ = callAndRead(
        ['ip', 'addr', 'add', self.ipv6_network, 'dev', self.name],
        raise_on_error=False)
      if code == 0:
        # address added to the interface - wait
        time.sleep(1)


class Interface(object):
  """Represent a network interface on the system"""

  def __init__(self, logger, name, ipv4_local_network, ipv6_interface=None, ipv6_prefixshift=16):
    """
    Attributes:
        name: String, the name of the interface
    """

    self._logger = logger
    self.name = str(name)
    self.ipv4_local_network = ipv4_local_network
    self.ipv6_interface = ipv6_interface or name
    self._ipv6_ranges = set()

    self.ipv6_prefixshift = ipv6_prefixshift

  # XXX no __getinitargs__, as instances of this class are never deserialized.

  def getIPv4LocalAddressList(self):
    """
    Returns currently configured local IPv4 addresses which are in
    ipv4_local_network
    """
    try:
      address_list = getNormalizedIfaddresses(self.name, socket.AF_INET)
    except KeyError: # No entry for socket.AF_INET
      return []
    return [
            {
              'addr': q['addr'],
              'netmask': q['netmask']
            }
            for q in address_list
            if netaddr.IPAddress(q['addr'], 4) in netaddr.glob_to_iprange(
                netaddr.cidr_to_glob(self.ipv4_local_network))
            ]

  def getGlobalScopeAddressList(self, tap=None):
    """Returns currently configured global scope IPv6 addresses"""
    interface_name = self.ipv6_interface
    try:
      address_list = [
          q
          for q in getNormalizedIfaddresses(interface_name, socket.AF_INET6)
          if isGlobalScopeAddress(q['addr'].split('%')[0])
      ]
    except KeyError:
      raise ValueError("%s must have at least one IPv6 address assigned" %
                         interface_name)
    if not address_list:
      raise NoAddressOnInterface(interface_name)

    if tap:
      try:
        address_list += [
          q
          for q in getNormalizedIfaddresses(tap.name, socket.AF_INET6)
          if isGlobalScopeAddress(q['addr'].split('%')[0])
      ]
      except KeyError:
        pass

    if sys.platform == 'cygwin':
      for q in address_list:
        q.setdefault('netmask', 'FFFF:FFFF:FFFF:FFFF::')
    # XXX: Missing implementation of Unique Local IPv6 Unicast Addresses as
    # defined in http://www.rfc-editor.org/rfc/rfc4193.txt
    # XXX: XXX: XXX: IT IS DISALLOWED TO IMPLEMENT link-local addresses as
    # Linux and BSD are possibly wrongly implementing it -- it is "too local"
    # it is impossible to listen or access it on same node
    # XXX: IT IS DISALLOWED to implement ad hoc solution like inventing node
    # local addresses or anything which does not exists in RFC!
    return address_list

  def _addSystemAddress(self, address, netmask, ipv6=True, tap=None):
    """Adds system address to interface

    Returns True if address was added successfully.

    Returns False if there was issue.
    """

    if ipv6:
      address_string = '%s/%s' % (address, lenNetmaskIpv6(netmask))
      af = socket.AF_INET6
      interface_name = self.ipv6_interface
    else:
      af = socket.AF_INET
      address_string = '%s/%s' % (address, netmaskToPrefixIPv4(netmask))
      interface_name = self.name

    if tap:
      interface_name = tap.name
    # check if address is already took by any other interface
    for interface in netifaces.interfaces():
      if interface != interface_name:
        address_dict = netifaces.ifaddresses(interface)
        if af in address_dict:
          if address in [q['addr'].split('%')[0] for q in address_dict[af]]:
            self._logger.warning('Cannot add address %s to %s as it already exists on interface %s.' % \
                (address, interface_name, interface))
            return False

    if not af in netifaces.ifaddresses(interface_name) \
        or not address in [q['addr'].split('%')[0]
                           for q in netifaces.ifaddresses(interface_name)[af]
                           ]:
      # add an address
      command = ['ip', 'addr', 'add', address_string, 'dev', interface_name]
      if tap and ipv6:
        # taps are routed manually via the first address in the range
        command.append('noprefixroute')
      code, _ = callAndRead(command)

      if code != 0:
        return False
      time.sleep(2)

    # Fake success for local ipv4
    if not ipv6:
      return True

    # check existence on interface for ipv6
    _, result = callAndRead(['ip', '-6', 'addr', 'list', interface_name])
    for l in result.split('\n'):
      if address in l:
        if 'tentative' in l and not tap:
          # duplicate, remove
          callAndRead(['ip', 'addr', 'del', address_string, 'dev', interface_name])
          return False
        # found and clean
        return True
    # even when added not found, this is bad...
    return False

  def _generateRandomIPv4Address(self, netmask):
    # no addresses found, generate new one
    # Try 10 times to add address, raise in case if not possible
    try_num = 10
    while try_num > 0:
      addr = random.choice([q for q in netaddr.glob_to_iprange(
        netaddr.cidr_to_glob(self.ipv4_local_network))]).format()
      if (dict(addr=addr, netmask=netmask) not in
            self.getIPv4LocalAddressList()):
        # Checking the validity of the IPv6 address
        if self._addSystemAddress(addr, netmask, False):
          return dict(addr=addr, netmask=netmask)
        try_num -= 1

    raise AddressGenerationError(addr)

  def addIPv4LocalAddress(self, addr=None):
    """Adds local IPv4 address in ipv4_local_network"""
    netmask = str(netaddr.IPNetwork(self.ipv4_local_network).netmask) if sys.platform == 'cygwin' \
             else '255.255.255.255'
    local_address_list = self.getIPv4LocalAddressList()
    if addr is None:
      return self._generateRandomIPv4Address(netmask)
    elif dict(addr=addr, netmask=netmask) not in local_address_list:
      if self._addSystemAddress(addr, netmask, False):
        return dict(addr=addr, netmask=netmask)
      else:
        self._logger.warning('Impossible to add old local IPv4 %s. Generating '
            'new IPv4 address.' % addr)
        return self._generateRandomIPv4Address(netmask)
    else:
      # confirmed to be configured
      return dict(addr=addr, netmask=netmask)

  def _checkIpv6Range(self, address, prefixlen):
    network = str(netaddr.IPNetwork("%s/%d" % (address, prefixlen)).cidr)
    if network in self._ipv6_ranges:
      self._logger.warning(
        "Address range %s/%d is already attributed", address, prefixlen)
      return False
    return True

  def _reserveIpv6Range(self, address, prefixlen):
    network = str(netaddr.IPNetwork("%s/%d" % (address, prefixlen)).cidr)
    assert(network not in self._ipv6_ranges)
    self._ipv6_ranges.add(network)

  def _tryReserveIpv6Range(self, address, prefixlen):
    if self._checkIpv6Range(address, prefixlen):
      self._reserveIpv6Range(address, prefixlen)
      return True
    return False

  def _generateRandomIPv6Addr(self, address_dict):
    netmask = address_dict['netmask']
    r = random.randint(1, 65000)
    addr = ':'.join(address_dict['addr'].split(':')[:-1] + ['%x' % r])
    socket.inet_pton(socket.AF_INET6, addr)
    return dict(addr=addr, netmask=netmask)

  def _generateRandomIPv6Range(self, address_dict, suffix):
    prefixlen = lenNetmaskIpv6(address_dict['netmask'])
    prefix = binFromIpv6(address_dict['addr'])[:prefixlen]
    prefixlen += 16
    if prefixlen >= 128:
      msg = 'Address range %r is too small for IPv6 subranges'
      self._logger.error(msg, address_dict)
      raise AddressGenerationError('%s/%d' % (address_dict['addr'], prefixlen))
    addr = ipv6FromBin(prefix
      + bin(random.randint(1, 65000))[2:].zfill(16)
      + suffix * (128 - prefixlen))
    return dict(addr=addr, prefixlen=prefixlen, netmask=netmaskFromLenIPv6(prefixlen))

  def addIPv6Address(self, partition_index, addr=None, netmask=None, tap=None):
    """
    Adds IPv6 address to interface.

    If addr is specified and exists already on interface, do nothing.

    If addr is specified and does not exist on interface, try to add given
    address. If it is not possible (ex. because network changed), calculate new
    address.

    If tap is specified, tap will get actually an IPv6 range (and not a single
    address) 16 bits smaller than the range of the interface.

    Args:
      addr: Wished address to be added to interface.
      netmask: Wished netmask to be used.
      tap: tap interface

    Returns:
      dict(addr=address, netmask=netmask).

    Raises:
      AddressGenerationError: Couldn't construct valid address with existing
          one's on the interface.
      NoAddressOnInterface: There's no address on the interface to construct
          an address with.
    """
    interface_name = self.ipv6_interface

    # Getting one address of the interface as base of the next addresses
    interface_addr_list = self.getGlobalScopeAddressList()
    address_dict = interface_addr_list[0]

    if addr is not None:
      # support netifaces which returns netmask and netmask/len
      # will result with updating the computer XML netmask only
      # to follow the change of netmask representation in netifaces
      if '/' in netmask:
        dict_addr_netmask_with_len = dict(addr=addr, netmask=netmask)
        dict_addr_netmask_without_len = dict(addr=addr, netmask=netmask.split('/')[0])
      else:
        dict_addr_netmask_without_len = dict(addr=addr, netmask=netmask)
        dict_addr_netmask_with_len = dict(addr=addr, netmask='%s/%s' % (netmask, lenNetmaskIpv6(netmask)))
      for dict_addr_netmask in [dict_addr_netmask_with_len, dict_addr_netmask_without_len]:
        if dict_addr_netmask in interface_addr_list or \
           (tap and dict_addr_netmask in self.getGlobalScopeAddressList(tap=tap)):
          # confirmed to be configured
          # return without len to keep format stable, as the first time len is not included
          return dict_addr_netmask_without_len
      if netmask == address_dict['netmask'] or \
         (tap and lenNetmaskIpv6(netmask) == 128):
        # same netmask, so there is a chance to add good one
        interface_network = netaddr.ip.IPNetwork('%s/%s' % (address_dict['addr'],
          lenNetmaskIpv6(address_dict['netmask'])))
        requested_network = netaddr.ip.IPNetwork('%s/%s' % (addr,
          lenNetmaskIpv6(address_dict['netmask'])))
        if interface_network.network == requested_network.network:
          # same network, try to add
          if self._addSystemAddress(addr, netmask, tap=tap):
            # succeed, return it
            self._logger.info('Successfully added IPv6 %s to %s.' % (addr, getattr(tap, 'name', None) or interface_name))
            return dict_addr_netmask
          else:
            self._logger.warning('Impossible to add old public IPv6 %s. '
                'Generating new IPv6 address.' % addr)

    # Try to use the IPv6 mapping based on partition index
    address_dict['prefixlen'] = lenNetmaskIpv6(address_dict['netmask'])
    if tap:
      result_addr = getTapIpv6Range(address_dict, partition_index, self.ipv6_prefixshift)
    else:
      result_addr = getPartitionIpv6Addr(address_dict, partition_index)
    result_addr['netmask'] = netmaskFromLenIPv6(result_addr['prefixlen'])
    if not tap or self._checkIpv6Range(result_addr['addr'], result_addr['prefixlen']):
      if self._addSystemAddress(result_addr['addr'], result_addr['netmask'], tap=tap):
        if tap:
          self._reserveIpv6Range(result_addr['addr'], result_addr['prefixlen'])
        return result_addr

    if self.ipv6_prefixshift != 16:
      self._logger.error(
        "Address %s/%s for partition %s is already taken;"
        " aborting because IPv6 prefixshift is %s != 16" % (
          result_addr['addr'],
          result_addr['prefixlen'],
          '%s tap' % partition_index if tap else partition_index,
          self.ipv6_prefixshift,
      ))
      raise AddressGenerationError(addr)

    self._logger.warning(
      "Falling back to random address selection for partition %s"
      " because %s/%s is already taken" % (
        '%s tap' % partition_index if tap else partition_index,
        result_addr['addr'],
        result_addr['prefixlen'],
      ))

    # Try 10 times to add address, raise in case if not possible
    for _ in range(10):
      if tap:
        result_addr = self._generateRandomIPv6Range(address_dict, suffix='1')
      else:
        result_addr = self._generateRandomIPv6Addr(address_dict)
      # Checking the validity of the IPv6 address
      addr = result_addr['addr']
      if not tap or self._checkIpv6Range(addr, result_addr['prefixlen']):
        if self._addSystemAddress(addr, result_addr['netmask'], tap=tap):
          if tap:
            self._reserveIpv6Range(addr, result_addr['prefixlen'])
          return result_addr

    raise AddressGenerationError(addr)

  def generateIPv6Range(self, i, tun=False):
    """
    Generate an IPv6 range included in the IPv6 range of the interface. The IPv6 range depends on the partition index i.

    Returns:
      dict(addr=address, netmask=netmask, network=addr/CIDR).

    Raises:
      ValueError: Couldn't construct valid address with existing
          one's on the interface.
      NoAddressOnInterface: There's no address on the interface to construct
          an address with.
    """
    interface_name = self.ipv6_interface or self.name

    # Getting one address of the interface as base of the next addresses
    interface_addr_list = self.getGlobalScopeAddressList()
    address_dict = interface_addr_list[0]
    address_dict['prefixlen'] = lenNetmaskIpv6(address_dict['netmask'])
    if tun:
      ipv6_range = getTunIpv6Range(address_dict, i, self.ipv6_prefixshift)
    else:
      ipv6_range = getPartitionIpv6Range(address_dict, i, self.ipv6_prefixshift)
    ipv6_range['netmask'] = netmaskFromLenIPv6(ipv6_range['prefixlen'])
    ipv6_range['network'] = '%(addr)s/%(prefixlen)d' % ipv6_range
    if self._tryReserveIpv6Range(ipv6_range['addr'], ipv6_range['prefixlen']):
      return ipv6_range

    if self.ipv6_prefixshift != 16:
      self._logger.error(
        "Address % for partition %s is already taken;"
        " aborting because IPv6 prefixshift is %s != 16" % (
          ipv6_range['network'],
          '%s tun' % i if tun else i,
          self.ipv6_prefixshift,
      ))
      raise AddressGenerationError(ipv6_range['addr'])

    self._logger.warning(
      "Falling back to random IPv6 range selection for partition %s"
      " because %s is already taken" % (
        '%s tun' % i if tun else i,
        ipv6_range['network'],
      ))

    # Try 10 times to add address, raise in case if not possible
    for _ in range(10):
      ipv6_range = self._generateRandomIPv6Range(address_dict, suffix='0')
      if self._tryReserveIpv6Range(ipv6_range['addr'], ipv6_range['prefixlen']):
        return ipv6_range
    raise AddressGenerationError(ipv6_range['addr'])

  def allowNonlocalBind(self):
    # This will allow the usage of unexisting IPv6 adresses.
    self._logger.debug('sysctl net.ipv6.ip_nonlocal_bind=1')
    callAndRead(['sysctl', 'net.ipv6.ip_nonlocal_bind=1'])

  def addLocalRouteIpv6Range(self, ipv6_range):
    # Add the IPv6 range to local route table

    # This will allow using the addresses in the range
    # even if they are not added anywhere.
    network = ipv6_range['network']

    _, result = callAndRead(['ip', '-6', 'route', 'show', 'table', 'local', network])
    if not 'dev lo' in result:
      self._logger.debug(' ip -6 route add local %s dev lo', network)
      callAndRead(['ip', '-6', 'route', 'add', 'local', network, 'dev', 'lo'])


def parse_computer_definition(conf, definition_path):
  conf.logger.info('Using definition file %r' % definition_path)
  computer_definition = configparser.RawConfigParser({
    'software_user': 'slapsoft',
  })
  computer_definition.read(definition_path)
  interface = None
  address = None
  netmask = None
  if computer_definition.has_option('computer', 'address'):
    address, netmask = computer_definition.get('computer', 'address').split('/')
  if (conf.alter_network and conf.interface_name is not None
        and conf.ipv4_local_network is not None):
    interface = Interface(logger=conf.logger,
                          name=conf.interface_name,
                          ipv4_local_network=conf.ipv4_local_network,
                          ipv6_interface=conf.ipv6_interface,
                          ipv6_prefixshift=conf.ipv6_prefixshift)
  computer = Computer(
      reference=conf.computer_id,
      interface=interface,
      addr=address,
      netmask=netmask,
      ipv6_interface=conf.ipv6_interface,
      partition_has_ipv6_range=conf.partition_has_ipv6_range,
      software_user=computer_definition.get('computer', 'software_user'),
      tap_gateway_interface=conf.tap_gateway_interface,
      tap_ipv6=conf.tap_ipv6,
      software_root=conf.software_root,
      instance_root=conf.instance_root
  )
  partition_list = []
  for partition_number in range(int(conf.partition_amount)):
    section = 'partition_%s' % partition_number
    user = User(computer_definition.get(section, 'user'))
    address_list = []
    for a in computer_definition.get(section, 'address').split():
      address, netmask = a.split('/')
      address_list.append(dict(addr=address, netmask=netmask))
    if computer_definition.has_option(section, 'ipv6_range'):
      ipv6_range_network = computer_definition.get(section, 'ipv6_range')
      ipv6_range_addr, ipv6_range_prefixlen = ipv6_range_network.split('/')
      ipv6_range_prefixlen = int(ipv6_range_prefixlen)
      ipv6_range_netmask = netmaskFromLenIPv6(ipv6_range_prefixlen)
      ipv6_range = {
        'addr' : ipv6_range_addr,
        'netmask' : ipv6_range_netmask,
        'network' : ipv6_range_network,
        'prefixlen': ipv6_range_prefixlen,
      }
    else:
      ipv6_range = {}
    tap = Tap(computer_definition.get(section, 'network_interface'))
    tun = Tun("slaptun" + str(partition_number),
              partition_number,
              int(conf.partition_amount, conf.tun_ipv6)) if conf.create_tun else None
    partition = Partition(reference=computer_definition.get(section, 'pathname'),
                          path=os.path.join(conf.instance_root,
                                            computer_definition.get(section, 'pathname')),
                          user=user,
                          address_list=address_list,
                          ipv6_range=ipv6_range,
                          tap=tap, tun=tun)
    if computer_definition.has_option(section, 'capability_list'):
      # Attribute .capability_list exists only when capabilities are defined
      capability_string = computer_definition.get(section, 'capability_list')
      capability_list = []
      for c in capability_string.splitlines():
          c = c.strip()
          if c:
            capability_list.append(c)
      partition.capability_list = capability_list
    partition_list.append(partition)
  computer.partition_list = partition_list
  return computer


def parse_computer_xml(conf, xml_path):
  interface = Interface(logger=conf.logger,
                        name=conf.interface_name,
                        ipv4_local_network=conf.ipv4_local_network,
                        ipv6_interface=conf.ipv6_interface,
                        ipv6_prefixshift=conf.ipv6_prefixshift)

  if os.path.exists(xml_path):
    conf.logger.debug('Loading previous computer data from %r' % xml_path)
    computer = Computer.load(xml_path,
                             reference=conf.computer_id,
                             ipv6_interface=conf.ipv6_interface,
                             partition_has_ipv6_range=conf.partition_has_ipv6_range,
                             tap_gateway_interface=conf.tap_gateway_interface,
                             tap_ipv6=conf.tap_ipv6,
                             software_root=conf.software_root,
                             instance_root=conf.instance_root,
                             config=conf)
    # Connect to the interface defined by the configuration
    computer.interface = interface
  else:
    # If no pre-existent configuration found, create a new computer object
    conf.logger.warning('Creating new computer data with id %r', conf.computer_id)
    computer = Computer(
      reference=conf.computer_id,
      software_root=conf.software_root,
      instance_root=conf.instance_root,
      interface=interface,
      addr=None,
      netmask=None,
      ipv6_interface=conf.ipv6_interface,
      partition_has_ipv6_range=conf.partition_has_ipv6_range,
      software_user=conf.software_user,
      tap_gateway_interface=conf.tap_gateway_interface,
      tap_ipv6=conf.tap_ipv6,
      config=conf,
    )

  partition_amount = int(conf.partition_amount)
  existing_partition_amount = len(computer.partition_list)

  if partition_amount < existing_partition_amount:
    conf.logger.critical('Requested amount of computer partitions (%s) is lower '
                         'than already configured (%s), cannot continue',
                         partition_amount, existing_partition_amount)
    sys.exit(1)
  elif partition_amount > existing_partition_amount:
    conf.logger.info('Adding %s new partitions',
                     partition_amount - existing_partition_amount)

  for i in range(existing_partition_amount, partition_amount):
    # add new partitions
    partition = Partition(
        reference='%s%s' % (conf.partition_base_name, i),
        path=os.path.join(conf.instance_root, '%s%s' % (
          conf.partition_base_name, i)),
        user=User('%s%s' % (conf.user_base_name, i)),
        address_list=None,
        ipv6_range=None,
        tap=Tap('%s%s' % (conf.tap_base_name, i)),
        tun=Tun('slaptun' + str(i), i, partition_amount, conf.tun_ipv6) if conf.create_tun else None
    )
    computer.partition_list.append(partition)

  return computer


def write_computer_definition(conf, computer):
  computer_definition = configparser.RawConfigParser()
  computer_definition.add_section('computer')
  if computer.address is not None and computer.netmask is not None:
    computer_definition.set('computer', 'address', '/'.join(
      [computer.address, computer.netmask]))
  for partition_number, partition in enumerate(computer.partition_list):
    section = 'partition_%s' % partition_number
    computer_definition.add_section(section)
    address_list = []
    for address in partition.address_list:
      address_list.append('/'.join([address['addr'], address['netmask']]))
    computer_definition.set(section, 'address', ' '.join(address_list))
    computer_definition.set(section, 'ipv6_range', partition.ipv6_range['network'])
    computer_definition.set(section, 'user', partition.user.name)
    computer_definition.set(section, 'network_interface', partition.tap.name)
    computer_definition.set(section, 'pathname', partition.reference)
  computer_definition.write(open(conf.output_definition_file, 'w'))
  conf.logger.info('Stored computer definition in %r' % conf.output_definition_file)


def random_delay(conf):
  # Add delay between 0 and 1 hour
  # XXX should be the contrary: now by default, and cron should have
  # --maximal-delay=3600
  if not conf.now:
    duration = float(60 * 60) * random.random()
    conf.logger.info('Sleeping for %s seconds. To disable this feature, '
                     'use with --now parameter in manual.' % duration)
    time.sleep(duration)


def do_format(conf):
  try:
    random_delay(conf)

    if conf.input_definition_file:
      computer = parse_computer_definition(conf, conf.input_definition_file)
    else:
      # no definition file, figure out computer
      computer = parse_computer_xml(conf, conf.computer_xml)

    computer.instance_storage_home = conf.instance_storage_home
    conf.logger.info('Updating computer')
    address = computer.getAddress()
    computer.address = address['addr']
    # Normalize netmask due to netiface netmasks like ffff::/16
    computer.netmask = address['netmask'] and address['netmask'].split('/')[0]

    if conf.output_definition_file:
      write_computer_definition(conf, computer)

    computer.format(alter_user=conf.alter_user,
                      alter_network=conf.alter_network,
                      create_tap=conf.create_tap)

    if getattr(conf, 'certificate_repository_path', None):
      mkdir_p(conf.certificate_repository_path, mode=0o700)

    computer.update()
    # Dumping and sending to the erp5 the current configuration
    if not conf.dry_run:
      computer.dump(path_to_xml=conf.computer_xml,
                    path_to_json=conf.computer_json,
                    logger=conf.logger)
    conf.logger.info('Posting information to %r' % conf.master_url)
    try:
      computer.send(conf)
      return FormatReturn.SUCCESS
    except Exception:
      conf.logger.exception('failed to transfer information to %r' % conf.master_url)
      return FormatReturn.OFFLINE_SUCCESS
    finally:
      conf.logger.info('slapos successfully prepared the computer.')
  except Exception:
    conf.logger.exception('slapos failed to prepare the computer.')
    return FormatReturn.FAILURE



class FormatConfig(object):
  """This class represents the options for slapos node format
  all the attributes of this class are options
  all the attributes can be modified by config file (.cfg)
  some attributes can be modified by command line"""

  # Network options
  alter_network = 'True' # modifiable by cmdline
  interface_name = None
  ipv6_interface = None
  partition_has_ipv6_range = True
  ipv6_prefixshift = 16
  create_tap = True
  tap_base_name = None
  tap_ipv6 = True
  tap_gateway_interface = ''
  ipv4_local_network = None
  create_tun = False
  tun_ipv6 = True

  # User options
  alter_user = 'True' # modifiable by cmdline
  software_user = 'slapsoft'
  instance_storage_home = None
  partition_base_name = None
  user_base_name = None

  # Other options
  input_definition_file = None  # modifiable by cmdline
  computer_xml = None           # modifiable by cmdline
  computer_json = None          # modifiable by cmdline
  log_file = None               # modifiable by cmdline
  output_definition_file = None # modifiable by cmdline
  dry_run = None                # modifiable by cmdline
  key_file = None
  cert_file = None

  def __init__(self, logger):
    self.logger = logger

  @staticmethod
  def checkRequiredBinary(binary_list):
    missing_binary_list = []
    for b in binary_list:
      if type(b) is not list:
        b = [b]
      try:
        callAndRead(b)
      except ValueError:
        pass
      except OSError:
        missing_binary_list.append(b[0])
    if missing_binary_list:
      raise UsageError('Some required binaries are missing or not '
          'functional: %s' % (','.join(missing_binary_list), ))

  def mergeConfig(self, args, configp):
    """
    Set options given by config files and arguments.
    Must be executed before setting up the logger.
    """
    # First, the configuration file options erase the default class options
    for section in ("slapformat", "slapos"):
      self.__dict__.update(configp.items(section))

    # Second, the command line arguments erase the configuration file options
    self.__dict__.update(args.__dict__)

  def setConfig(self):
    # deprecated options raise an error
    for option in ['bridge_name', 'no_bridge']:
      if getattr(self, option, None):
        message = 'Option %r is totally deprecated, please update your config file' % (option)
        self.logger.error(message)
        raise UsageError(message)

    # Convert strings to booleans
    for option in ['alter_network', 'alter_user', 'partition_has_ipv6_range', 'create_tap', 'create_tun', 'tap_ipv6', 'tun_ipv6']:
      attr = getattr(self, option)
      if isinstance(attr, str):
        if attr.lower() == 'true':
          root_needed = True
          setattr(self, option, True)
        elif attr.lower() == 'false':
          setattr(self, option, False)
        else:
          message = 'Option %r needs to be "True" or "False", wrong value: ' \
              '%r' % (option, getattr(self, option))
          self.logger.error(message)
          raise UsageError(message)

    if not self.dry_run:
      if self.alter_user:
        self.checkRequiredBinary(['groupadd', 'useradd', 'usermod', ['passwd', '-h']])
      if self.create_tap or self.alter_network:
        self.checkRequiredBinary(['ip'])

    # Check mandatory options
    for parameter in ('computer_id', 'instance_root', 'master_url',
                      'software_root', 'computer_xml'):
      if not getattr(self, parameter, None):
        raise UsageError("Parameter '%s' is not defined." % parameter)

    # Check existence of SSL certificate files, if defined
    for attribute in ['key_file', 'cert_file', 'master_ca_file']:
      file_location = getattr(self, attribute, None)
      if file_location is not None:
        if not os.path.exists(file_location):
          self.logger.fatal('File %r does not exist or is not readable.' %
              file_location)
          sys.exit(1)

    # Sanity check for prefixshift
    self.ipv6_prefixshift = ipv6_prefixshift = int(self.ipv6_prefixshift)
    if (1 << ipv6_prefixshift) < 4 * int(self.partition_amount):
        # Each partition needs at least 4 IPv6, for IPv6 address, range, tap and tun
        self.logger.fatal(
            'ipv6_prefixshift %s is too small for partition_amount %s',
            ipv6_prefixshift, self.partition_amount)
        sys.exit(1)

    self.logger.debug('Started.')
    if self.dry_run:
      self.logger.info("Dry-run mode enabled.")
    if self.create_tap:
      self.logger.info("Tap creation mode enabled (%s IPv6).", "with" if self.tap_ipv6 else "without")

    # Calculate path once
    self.computer_xml = os.path.abspath(self.computer_xml)

    if self.input_definition_file:
      self.input_definition_file = os.path.abspath(self.input_definition_file)

    if self.output_definition_file:
      self.output_definition_file = os.path.abspath(self.output_definition_file)


tracing_monkeypatch_mark = []
def tracing_monkeypatch(conf):
  """Substitute os module and callAndRead function with tracing wrappers."""

  # This function is called again if "slapos node boot" failed.
  # Don't wrap the logging method again, otherwise the output becomes double.
  if tracing_monkeypatch_mark:
    return

  global os
  global callAndRead

  real_callAndRead = callAndRead

  os = OS(conf)
  if conf.dry_run:
    def dry_callAndRead(argument_list, raise_on_error=True):
      return 0, ''
    callAndRead = dry_callAndRead

    def fake_getpwnam(user):
      class result(object):
        pw_uid = 12345
        pw_gid = 54321
      return result
    pwd.getpwnam = fake_getpwnam
  else:
    dry_callAndRead = real_callAndRead

  def logging_callAndRead(argument_list, raise_on_error=True):
    conf.logger.debug(' '.join(argument_list))
    return dry_callAndRead(argument_list, raise_on_error)
  callAndRead = logging_callAndRead

  # Put a mark. This function was called once.
  tracing_monkeypatch_mark.append(None)
