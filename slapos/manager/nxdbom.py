# coding: utf-8
import logging
import os
import shlex
import subprocess


from zope.interface import implementer
from slapos.manager import interface

logger = logging.getLogger(__name__)


@implementer(interface.IManager)
class Manager(object):
  """Runs nxd-bom after running software installation.
  """
  def __init__(self, config):
    self.config = config

  def software(self, software):
    pass

  def softwareTearDown(self, software):
    installation_time = os.stat(
      os.path.join(software.software_path, '.completed')).st_mtime

    for f, o in (
      ('text', 'nxdbom.txt'),
      ('cyclonedx-json', 'nxdbom.cdx.json'),
    ):
      output_file = os.path.join(software.software_path, o)
      if os.path.exists(output_file) \
          and os.stat(output_file).st_mtime >= installation_time:
        logger.debug('%s already up to date', output_file)
        continue

      args = [
        'nxdbom',
        '--format',
        f,
        '--output',
        output_file,
        'software',
        software.software_path,
      ]
      cmd = ' '.join([shlex.quote(a) for a in args])
      logger.info('Running: %s', cmd)
      subprocess.check_call(args)

  def format(self, computer):
    pass

  def formatTearDown(self, computer):
    pass

  def instance(self, partition):
    pass

  def instanceTearDown(self):
    pass
