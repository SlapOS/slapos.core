# coding: utf-8
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

  def instanceTearDown(self, partition):
    """Method  called after `slapos node instance` phase.

    :param partition: slapos.grid.SlapObject.Partition, processed partition
    """
    if self.config is None:
      logger.warning(
        '[firewall] missing in the configuration, manager disabled.')
      return
    whitelist_firewall_path = os.path.join(
      partition.instance_path, self.whitelist_firewall_filename)
    if not os.path.exists(whitelist_firewall_path):
      logger.debug(
        'File %s does not exists, ignoring partition %s.',
        whitelist_firewall_path, partition.partition_id)
      return

    with open(whitelist_firewall_path) as f:
      try:
        ip_list = sorted(json.load(f))
        assert isinstance(ip_list, list)
      except Exception:
        logger.warning(
          'Bad whitelist firewall config %', whitelist_firewall_path,
          exc_info=True)
        return

    logger.info('Configuring partition %s.', partition.partition_id)
    user_id = partition.getUserGroupId()[0]
    chain_name = '%s-whitelist' % (partition.partition_id,)

    def fwCommunicate(arg_list):
      return fexecute(
        [self.config['firewall_cmd'], '--direct', '--permanent'] + arg_list
      )

    chain_cmd = ['ipv4', 'filter', chain_name]
    if fwCommunicate(['--query-chain'] + chain_cmd)[1].strip() != 'yes':
      fwCommunicate(['--add-chain'] + chain_cmd)
    # XXX - descriptive chain name with a hash is too big for chain name
    #       limits, thus removal and readd
    fwCommunicate(['--remove-rules', 'ipv4', 'filter', chain_name])
    for ip in ip_list:
      # whitelist what is expected
      fwCommunicate([
        '--add-rule', 'ipv4', 'filter', chain_name, '0', '-d', ip, '-j',
        'ACCEPT'])
    # drop everything else
    fwCommunicate([
      '--add-rule', 'ipv4', 'filter', chain_name, '0', '-j', 'REJECT'])
    # configure the rule for the user to whitelist the partition access
    rule_cmd = [
      'ipv4', 'filter', 'OUTPUT', '0', '-m', 'owner', '--uid-owner',
      str(user_id), '-j', chain_name]
    if fwCommunicate(['--query-rule'] + rule_cmd)[1].strip() != 'yes':
      fwCommunicate(['--add-rule'] + rule_cmd)
    subprocess.check_output([self.config['firewall_cmd'], '--reload'])

  def report(self, partition):
    """Method called at `slapos node report` phase.

    :param partition: slapos.grid.SlapObject.Partition, currently processed
                      partition
    """
