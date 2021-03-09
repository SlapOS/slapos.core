# coding: utf-8
import json
import logging
import os
import hashlib

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

    # make hash of the ip_list
    # compose expected: partition.partition_id-<hash>, remember as chain
    # if chain exist and is configured in filter table as expected do nothing
    # if chain does not exists:
    #  * add such chain which defaults to reject but allows all IPs on OUTPT
    #  * add such chain to the filter table
    #  * remove all others chains partition.partition_id-<not-this-hash> with their configuration
    # rememeber: it's safe to raise here, it'll result with Error while processing the following partitions: slappartN[<softwaretype>]:         
    raise NotImplementedError

  def report(self, partition):
    """Method called at `slapos node report` phase.

    :param partition: slapos.grid.SlapObject.Partition, currently processed partition
    """
