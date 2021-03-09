# coding: utf-8
import hashlib
import json
import logging
import os
import subprocess

from .interface import IManager
from zope.interface import implementer

logger = logging.getLogger(__name__)


@implementer(IManager)
class Manager(object):
  whitelist_firewall_filename = '.slapos-whitelist-firewall'

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

    :param software: slapos.grid.SlapObject.Software, currently processed software
    """

  def softwareTearDown(self, software):
    """Method called after `slapos node software` phase.

    :param computer: slapos.grid.SlapObject.Software, processed software
    """

  def instance(self, partition):
    """Method called at `slapos node instance` phase.

    :param partition: slapos.grid.SlapObject.Partition, currently processed partition
    """

  def instanceTearDown(self, partition):
    """Method  called after `slapos node instance` phase.

    :param partition: slapos.grid.SlapObject.Partition, processed partition
    """
    if self.config is None:
      logger.warning('[firewall] missing in the configuration, manager disabled.')
      return
    whitelist_firewall_path = os.path.join(
      partition.instance_path, self.whitelist_firewall_filename)
    if not os.path.exists(whitelist_firewall_path):
      return

    with open(whitelist_firewall_path) as f:
      try:
        ip_list = sorted(json.load(f))
        assert isinstance(ip_list, list)
      except Exception:
        logger.warning('Bad whitelist firewall config file', exc_info=True)
        return

    user_id = partition.getUserGroupId()[0]
    chain_name = '%s-whitelist' % (partition.partition_id,)
    fw_base_cmd = self.config['firewall_cmd']

    def fwCommunicate(arg_list):
      return subprocess.check_output(
        [self.config['firewall_cmd'], '--direct', '--permanent'] + arg_list
      )

    fwCommunicate(['--add-chain', 'ipv4', 'filter', chain_name])
    fwCommunicate(['--remove-rules', 'ipv4', 'filter', chain_name])
    for ip in ip_list:
      fwCommunicate(['--add-rule', 'ipv4', 'filter', chain_name, '0', '-p', 'tcp', '-d', ip, '-j', 'ACCEPT'])
    fwCommunicate(['--add-rule', 'ipv4', 'filter', chain_name, '0', '-j', 'REJECT'])
    fwCommunicate(['--add-rule', 'ipv4', 'filter', 'OUTPUT', '0', '-m', 'owner', '--uid-owner', str(user_id), '-j', chain_name])
    subprocess.check_output([self.config['firewall_cmd'], '--reload'])

  def report(self, partition):
    """Method called at `slapos node report` phase.

    :param partition: slapos.grid.SlapObject.Partition, currently processed partition
    """
