# coding: utf-8
import json
import logging
import os

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
        ip_list = json.load(f)
        assert isinstance(ip_list, list)
      except Exception:
        logger.warning('Bad whitelist firewall config file', exc_info=True)
        return

    import ipdb ; ipdb.set_trace()
    logger.warning('NotImplementedError')

  def report(self, partition):
    """Method called at `slapos node report` phase.

    :param partition: slapos.grid.SlapObject.Partition, currently processed partition
    """
