# coding: utf-8
import json
import logging
import os
import pwd
import grp
from .interface import IManager
from zope import interface

logger = logging.getLogger(__name__)

class Manager(object):
  interface.implements(IManager)

  disk_device_filename = '.slapos-disk-permission'

  def __init__(self, config):
    """Manager needs to know config for its functioning.
    """
    self.config = config

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
      except:
        logger.warning('Bad disk configuration file', exc_info=True)
        return

    for entry in disk_list:
      disk = entry.get("disk", None)
      if disk is None:
        logger.warning("Disk is None: %s " % disk_list, exc_info=True)
        continue

      if not str(disk).startswith("/dev/"):
        logger.warning("Bad disk definition: %s " % disk_list, exc_info=True)
        continue

      if len(disk[len("/dev/"):]) > 6:
        logger.warning("Bad disk definition: %s " % disk_list, exc_info=True)
        continue

      if not os.path.exists(disk):
        logger.warning("Disk don't exist: %s " % disk_list, exc_info=True)
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
