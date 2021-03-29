# coding: utf-8
# Copyright (C) 2021  Nexedi SA and Contributors.
#                     Łukasz Nowak <luke@nexedi.com>
#
# This program is free software: you can Use, Study, Modify and Redistribute
# it under the terms of the GNU General Public License version 3, or (at your
# option) any later version, as published by the Free Software Foundation.
#
# You can also Link and Combine this program with other software covered by
# the terms of any of the Free Software licenses or any of the Open Source
# Initiative approved licenses and Convey the resulting work. Corresponding
# source of such a combination shall include the source code for all other
# software used.
#
# This program is distributed WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See COPYING file for full licensing terms.
# See https://www.nexedi.com/licensing for rationale and options.

import hashlib
import ipaddress
import json
import logging
import os
import subprocess

from .interface import IManager
from zope.interface import implementer

logger = logging.getLogger(__name__)


# stolen from slapos/grid/slapgrid.py
class FPopen(subprocess.Popen):
  def __init__(self, *args, **kwargs):
    kwargs['stdin'] = subprocess.PIPE
    kwargs['stderr'] = subprocess.STDOUT
    kwargs.setdefault('stdout', subprocess.PIPE)
    kwargs.setdefault('close_fds', True)
    kwargs.setdefault('shell', False)
    subprocess.Popen.__init__(self, *args, **kwargs)
    self.stdin.flush()
    self.stdin.close()
    self.stdin = None


def fexecute(arg_list):
  process = FPopen(arg_list, universal_newlines=True)
  result, _ = process.communicate()
  return process.returncode, result


@implementer(IManager)
class Manager(object):
  whitelist_firewall_filename = '.slapos-whitelist-firewall'
  whitelist_firewall_md5sum = '.slapos-whitelist-firewall.md5sum'

  def __init__(self, config):
    """Manager needs to know config for its functioning.
    """
    self.config = 'firewall' in config and config['firewall'] or None

  def format(self, computer):
    """Method called at `slapos node format` phase.

    :param computer: slapos.format.Computer, currently formatted computer
    """

  def formatTearDown(self, computer):
    """Method called after `slapos node format` phase.

    :param computer: slapos.format.Computer, formatted computer
    """

  def software(self, software):
    """Method called at `slapos node software` phase.

    :param software: slapos.grid.SlapObject.Software, currently processed
                     software
    """

  def softwareTearDown(self, software):
    """Method called after `slapos node software` phase.

    :param computer: slapos.grid.SlapObject.Software, processed software
    """

  def instance(self, partition):
    """Method called at `slapos node instance` phase.

    :param partition: slapos.grid.SlapObject.Partition, currently processed
                      partition
    """

  def _fwCommunicate(self, arg_list):
    return fexecute(
      [self.config['firewall_cmd'], '--direct', '--permanent'] + arg_list
    )[1]

  def _reloadFirewalld(self):
    return_code, output = fexecute([self.config['firewall_cmd'], '--reload'])
    if return_code != 0:
      raise ValueError('Problem while reloading firewalld: %s', output)

  def _cleanUpPartitionFirewall(self, partition):
    chain_name = '%s-whitelist' % (partition.partition_id,)
    chain_cmd = ['ipv4', 'filter', chain_name]
    user_id = partition.getUserGroupId()[0]

    reload_firewall = False
    if self._fwCommunicate(['--query-chain'] + chain_cmd).strip() == 'yes':
      self._fwCommunicate(['--remove-rules', 'ipv4', 'filter', chain_name])
      self._fwCommunicate(['--remove-chain'] + chain_cmd)
      reload_firewall = True
    rule_cmd = [
      'ipv4', 'filter', 'OUTPUT', '0', '-m', 'owner', '--uid-owner',
      str(user_id), '-j', chain_name]
    if self._fwCommunicate(['--query-rule'] + rule_cmd).strip() == 'yes':
      self._fwCommunicate(['--remove-rule'] + rule_cmd)
      reload_firewall = True
    if reload_firewall:
      self._reloadFirewalld()
    return reload_firewall

  def instanceTearDown(self, partition):
    """Method  called after `slapos node instance` phase.

    :param partition: slapos.grid.SlapObject.Partition, processed partition
    """
    if self.config is None:
      logger.warning(
        '[firewall] missing in the configuration, manager disabled.')
      return

    chain_name = '%s-whitelist' % (partition.partition_id,)
    chain_cmd = ['ipv4', 'filter', chain_name]
    user_id = partition.getUserGroupId()[0]

    whitelist_firewall_md5sum_path = os.path.join(
      partition.instance_path, self.whitelist_firewall_md5sum)
    whitelist_firewall_path = os.path.join(
      partition.instance_path, self.whitelist_firewall_filename)

    if not os.path.exists(whitelist_firewall_path):
      if self._cleanUpPartitionFirewall(partition):
        logger.info(
          'File %s does not exists, removed configuration for partition %s.',
          whitelist_firewall_path, partition.partition_id)
      if os.path.exists(whitelist_firewall_md5sum_path):
        os.unlink(whitelist_firewall_md5sum_path)
      return

    with open(whitelist_firewall_path, 'rb') as fh:
      whitelist_firewall_path_md5sum = hashlib.md5(fh.read()).hexdigest()
    with open(whitelist_firewall_path) as f:
      try:
        json_list = json.load(f)
        assert isinstance(json_list, list)
        ip_list = []
        for ip in json_list:
          try:
            ip_address = ipaddress.ip_address(ip)
            if ip_address.version == 4:
              ip_list.append(str(ip_address.exploded))
            else:
              logger.warning('Entry %r is not an IPv4', ip)
          except Exception:
            logger.warning('Entry %r is not a real IP', ip)
      except Exception:
        logger.warning(
          'Bad whitelist firewall config %s', whitelist_firewall_path,
          exc_info=True)
        return

    try:
      with open(whitelist_firewall_md5sum_path, 'rb') as fh:
        previous_md5sum = fh.read().strip()
    except Exception:
      # whatever happened, it means that md5sum became unreadable, so
      # simply reset previous md5sum
      previous_md5sum = b''

    logger.info('Configuring partition %s.', partition.partition_id)
    chain_added = False
    if self._fwCommunicate(['--query-chain'] + chain_cmd).strip() != 'yes':
      self._fwCommunicate(['--add-chain'] + chain_cmd)
      chain_added = True
    if chain_added or \
       whitelist_firewall_path_md5sum != previous_md5sum.decode('utf-8'):
      with open(whitelist_firewall_md5sum_path, 'wb') as fh:
        # enforce re-add rules on next run, if any problem would be
        # encountered
        fh.write(b'')
      self._fwCommunicate(['--remove-rules', 'ipv4', 'filter', chain_name])
      for ip in ip_list:
        # whitelist what is expected
        self._fwCommunicate([
          '--add-rule', 'ipv4', 'filter', chain_name, '0', '-d', ip, '-j',
          'ACCEPT'])
      # drop everything else
      self._fwCommunicate([
        '--add-rule', 'ipv4', 'filter', chain_name, '0', '-j', 'REJECT'])
      # configure the rule for the user to whitelist the partition access
      rule_cmd = [
        'ipv4', 'filter', 'OUTPUT', '0', '-m', 'owner', '--uid-owner',
        str(user_id), '-j', chain_name]
      if self._fwCommunicate(['--query-rule'] + rule_cmd).strip() != 'yes':
        self._fwCommunicate(['--add-rule'] + rule_cmd)
      self._reloadFirewalld()
      with open(whitelist_firewall_md5sum_path, 'wb') as fh:
        # "commit" changes to the md5sum file
        fh.write(whitelist_firewall_path_md5sum.encode())
      logger.info('Updated rules for partition %s.', partition.partition_id)
    else:
      logger.debug(
        'Skipped up-to-date rules for partition %s.', partition.partition_id)

  def report(self, partition):
    """Method called at `slapos node report` phase.

    :param partition: slapos.grid.SlapObject.Partition, currently processed
                      partition
    """
    if self._cleanUpPartitionFirewall(partition):
      logger.info(
        'Cleaned up firewall for partition %s.', partition.partition_id)
    whitelist_firewall_md5sum_path = os.path.join(
      partition.instance_path, self.whitelist_firewall_md5sum)
    if os.path.exists(whitelist_firewall_md5sum_path):
      os.unlink(whitelist_firewall_md5sum_path)
