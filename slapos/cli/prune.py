# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2019 Vifib SARL and Contributors.
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

import sys
import glob
import os
import six.moves.configparser as configparser

from slapos.cli.config import ConfigCommand
from slapos.grid.slapgrid import merged_options


class PruneCommand(ConfigCommand):
  """Clean up unused shared slapos.recipe.cmmi parts.

  This simple script does not detect inter-dependencies and needs to run
  multiple times. For example, if A depend on B, when B is not used, B will
  be removed on first run and A will then become unused.
  """
  command_group = 'node'

  def get_parser(self, prog_name):
    ap = super(PruneCommand, self).get_parser(prog_name)
    ap.add_argument(
        '--dry-run', help="Don't delete, just log", action='store_true')
    return ap

  def take_action(self, args):
    configp = self.fetch_config(args)
    options = merged_options(args, configp)

    if not options.get('shared_part_list'):
      self.app.log.error('No shared_part_list options in slapos config')
      sys.exit(-1)

    pidfile_software = options.get('pidfile_software')
    if not args.dry_run and pidfile_software and os.path.exists(
        pidfile_software):
      self.app.log.error('Cannot prune while software is running')
      sys.exit(-1)

    sys.exit(do_prune(self.app.log, options, args.dry_run))


def do_prune(logger, options, dry_run):
  shared_root = options['shared_part_list'].splitlines()[-1].strip()
  logger.warning("Pruning shared directories at %s", shared_root)

  signatures = getUsageSignatureFromSoftwareAndSharedPart(
      logger, options['software_root'], shared_root)

  # recursively look in instance
  signatures.update(getUsageSignaturesFromSubInstance(logger, options['instance_root']))

  for shared_part in glob.glob(os.path.join(shared_root, '*', '*')):
    logger.debug("checking shared part %s", shared_part)
    h = os.path.basename(shared_part)
    for soft, installed_cfg in signatures.items():
      if h in installed_cfg:
        logger.debug("It is used in %s", soft)
        break
    else:
      if not dry_run:
        rmtree(shared_part)
      logger.warning(
          'Unusued shared parts at %s%s', shared_part,
          '' if dry_run else ' ... removed')


def getUsageSignaturesFromSubInstance(logger, instance_root):
  """Look at instances in instance_root to find used shared parts,
  if instances are recursive slapos.

  The heuristic is that if an instance contain a file named slapos.cfg,
  this is a recursive slapos.
  """
  signatures = {}
  for slapos_cfg in getInstanceSlaposCfgList(logger, instance_root):
    cfg = readSlaposCfg(logger, slapos_cfg)
    shared_root = None
    if cfg['shared_part_list']:
      shared_root = cfg['shared_part_list'][-1]
    signatures.update(
        getUsageSignatureFromSoftwareAndSharedPart(
            logger, cfg['software_root'], shared_root))
    signatures.update(
        getUsageSignaturesFromSubInstance(logger, cfg['instance_root'])
    )
  return signatures


def getInstanceSlaposCfgList(logger, instance_root):
  """Find all slapos.cfg from instance directory, as instance
  can contain recursive slapos (that refer parts from outer slapos).
  """
  for root, _, filenames in os.walk(instance_root):
    if 'slapos.cfg' in filenames:
      yield os.path.join(root, 'slapos.cfg')


def readSlaposCfg(logger, path):
  """Read a slapos.cfg found in an instance directory.
  """
  logger.debug('Reading config at %s', path)
  parser = configparser.ConfigParser({'shared_part_list': ''})
  parser.read([path])
  cfg = {
      'software_root': parser.get('slapos', 'software_root'),
      'instance_root': parser.get('slapos', 'instance_root'),
      'shared_part_list': parser.get('slapos', 'shared_part_list').splitlines()
  }
  logger.debug('Read config: %s', cfg)
  return cfg


def getUsageSignatureFromSoftwareAndSharedPart(
    logger, software_root, shared_root):
  """Look in all softwares and shared parts to collect the signatures
  that are used.
  """
  signatures = {}
  for installed_cfg in glob.glob(os.path.join(software_root, '*',
                                              '.installed.cfg')):
    with open(installed_cfg) as f:
      signatures[installed_cfg] = f.read()
  for script in glob.glob(os.path.join(software_root, '*', 'bin', '*')):
    with open(script) as f:
      signatures[script] = f.read()
  if shared_root:
    for shared_signature in glob.glob(os.path.join(shared_root, '*', '*',
                                                  '.*signature')):
      with open(shared_signature) as f:
        signatures[shared_signature] = f.read()
  return signatures



# XXX copied from https://lab.nexedi.com/nexedi/erp5/blob/31804f683fd36322fb38aeb9654bee70cebe4fdb/erp5/util/testnode/Utils.py
# TODO: move to shared place or ... isn't there already such an utility function in slapos.core ?
import shutil
import errno
import six
from six.moves import map

try:
  PermissionError
except NameError:  # make pylint happy on python2...
  PermissionError = Exception


def rmtree(path):
  """Delete a path recursively.
  Like shutil.rmtree, but supporting the case that some files or folder
  might have been marked read only.  """
  def chmod_retry(func, failed_path, exc_info):
    """Make sure the directories are executable and writable.
    """
    # Depending on the Python version, the following items differ.
    if six.PY3:
      expected_error_type = PermissionError
      expected_func = os.lstat
    else:
      expected_error_type = OSError
      expected_func = os.listdir
    e = exc_info[1]
    if isinstance(e, expected_error_type):
      if e.errno == errno.ENOENT:
        # because we are calling again rmtree on listdir errors, this path might
        # have been already deleted by the recursive call to rmtree.
        return
      if e.errno == errno.EACCES:
        if func is expected_func:
          os.chmod(failed_path, 0o700)
          # corner case to handle errors in listing directories.
          # https://bugs.python.org/issue8523
          return shutil.rmtree(failed_path, onerror=chmod_retry)
        # If parent directory is not writable, we still cannot delete the file.
        # But make sure not to change the parent of the folder we are deleting.
        if failed_path != path:
          os.chmod(os.path.dirname(failed_path), 0o700)
          return func(failed_path)
    raise e  # XXX make pylint happy

  shutil.rmtree(path, onerror=chmod_retry)
# / erp5/util/testnode/Utils.py code
