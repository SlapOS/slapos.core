# coding: utf-8
import json
import logging
import os
import pwd
import grp
import subprocess
from zope.interface import implementer
from slapos.manager import interface

logger = logging.getLogger(__name__)


@implementer(interface.IManager)
class Manager(object):
  disk_device_filename = '.slapos-disk-permission'

  def __init__(self, config):
    """Manager needs to know config for its functioning.
    """
    self.config = config
    self.allowed_disk_for_vm = None
    if 'manager' in config:
      if 'devperm' in config['manager']:
        if 'allowed-disk-for-vm' in config['manager']['devperm']:
          self.allowed_disk_for_vm = []
          for line in config[
            'manager']['devperm']['allowed-disk-for-vm'].splitlines():
            line = line.strip()
            if line:
              self.allowed_disk_for_vm.append(line)

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
    self.instanceTearDown(partition)

  def _getLsblkJsonDict(self):
    try:
      lsblk_json_dict = json.loads(subprocess.check_output([
        'lsblk', '--json', '--output-all']))
    except Exception:
      logger.info('lsblk call failed', exc_info=True)
      return {}
    if not isinstance(lsblk_json_dict, dict):
      logger.info('lsblk output not supported')
      return {}
    return lsblk_json_dict

  def _getLsblkDiskList(self):
    lsblk_dict = self._getLsblkJsonDict()

    if 'blockdevices' not in lsblk_dict:
      logger.info('lsblk output not supported')
      return []

    if not isinstance(lsblk_dict['blockdevices'], list):
      logger.info('lsblk output not supported')

    disk_list = []
    for block_device in lsblk_dict['blockdevices']:
      if 'path' in block_device and 'type' in block_device:
        if block_device['type'] == 'disk':
          disk_list.append(block_device['path'])
        if 'children' in block_device and isinstance(block_device['children'], list):
          for partition in block_device['children']:
            if 'path' in partition and 'type' in partition:
              if partition['type'] == 'part':
                disk_list.append(partition['path'])
    return disk_list

  def instanceTearDown(self, partition):
    """Method  called after `slapos node instance` phase.

    :param partition: slapos.grid.SlapObject.Partition, processed partition
    """
    disk_dev_path = os.path.join(partition.instance_path, self.disk_device_filename)
    if not os.path.exists(disk_dev_path):
      return

    # Read it
    with open(disk_dev_path) as f:
      try:
        disk_list = json.load(f)
      except Exception:
        logger.warning('Bad disk configuration file', exc_info=True)
        return

    lsblk_disk_list = self._getLsblkDiskList()
    for entry in disk_list:
      disk = entry.get("disk", None)
      if disk is None:
        logger.warning("Disk is None: %s " % disk_list, exc_info=True)
        continue

      disk = str(disk)
      original = disk
      try:
        while os.path.islink(disk):
          disk = os.readlink(disk)
      except OSError:
        logger.warning("Problem resolving link: %s " % original, exc_info=True)
        continue

      if self.allowed_disk_for_vm is not None:
        if disk not in self.allowed_disk_for_vm:
          logger.warning('Disk %s not in allowed disk list %s', disk, ', '.join(self.allowed_disk_for_vm))
          continue

      if disk not in lsblk_disk_list:
        logger.warning("Disk %r is not detected by lsblk list %r", disk, lsblk_disk_list)
        continue

      uid = os.stat(partition.instance_path).st_uid
      if os.stat(disk).st_uid == uid:
        continue

      logger.warning("Transfer ownership of %s to %s" % (disk, pwd.getpwuid(uid).pw_name))
      os.chown(disk, uid, grp.getgrnam("disk").gr_gid)

  def report(self, partition):
    """Method called at `slapos node report` phase.

    :param partition: slapos.grid.SlapObject.Partition, currently processed partition
    """
