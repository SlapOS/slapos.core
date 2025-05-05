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
from fnmatch import fnmatchcase
import six.moves.configparser as configparser

from slapos.cli.command import check_root_user
from slapos.cli.config import ConfigCommand
from slapos.grid.slapgrid import merged_options
from slapos.grid.utils import setRunning, setFinished
from slapos.util import rmtree, string_to_boolean


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

    if string_to_boolean(options.get('root_check', 'True').lower()):
      check_root_user(self)

    pidfile_software = options.get('pidfile_software')
    if not args.dry_run and pidfile_software and os.path.exists(
        pidfile_software):
      self.app.log.error('Cannot prune while software is running')
      sys.exit(-1)

    if pidfile_software:
      setRunning(logger=self.app.log, pidfile=pidfile_software)
    try:
      do_prune(self.app.log, options, args.dry_run)
    finally:
      if pidfile_software:
        setFinished(pidfile_software)


def _prune(
    logger,
    shared_root,
    software_root,
    instance_root,
    ignored_shared_parts,
    dry_run,
):
  signatures = getUsageSignatureFromSoftwareAndSharedPart(
      logger, software_root, shared_root, ignored_shared_parts)

  # recursively look in instance
  signatures.update(getUsageSignaturesFromSubInstance(
    logger, instance_root, set()))

  for shared_part in glob.glob(os.path.join(shared_root, '*', '*')):
    if shared_part not in ignored_shared_parts:
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
            'Unused shared parts at %s%s', shared_part,
            '' if dry_run else ' ... removed')
        yield shared_part


def _prune_loop(logger, shared_root, software_root, instance_root, dry_run):
  ignored_shared_parts = set()
  while True:
    pruned = list(
        _prune(
            logger,
            shared_root,
            software_root,
            instance_root,
            ignored_shared_parts,
            dry_run,
        ))
    if not pruned:
      break
    ignored_shared_parts.update(pruned)


def do_prune(logger, options, dry_run):
  shared_root = options['shared_part_list'].splitlines()[-1].strip()
  logger.warning("Pruning shared directories at %s", shared_root)
  _prune_loop(
      logger,
      shared_root,
      options['software_root'],
      options['instance_root'],
      dry_run,
  )


def getUsageSignaturesFromSubInstance(logger, instance_root, visited):
  """Look at instances in instance_root to find used shared parts,
  if instances are recursive slapos.

  The heuristic is that if an instance contain a file named slapos.cfg,
  this is a recursive slapos.
  """
  signatures = {}
  # prevent infinite loops
  if instance_root in visited:
    return signatures
  visited.add(instance_root)

  for slapos_cfg in getInstanceSlaposCfgList(logger, instance_root):
    cfg = readSlaposCfg(logger, slapos_cfg)
    if not cfg:
      continue
    shared_root = None
    if cfg['shared_part_list']:
      shared_root = cfg['shared_part_list'][-1]
      if not os.path.exists(shared_root):
        logger.debug(
            "Ignoring non existant shared root %s from %s",
            shared_root,
            slapos_cfg,
        )
        shared_root = None

    if not os.path.exists(cfg['software_root']):
      logger.debug(
          "Ignoring non existant software root %s from %s",
          cfg['software_root'],
          slapos_cfg,
      )
    else:
      signatures.update(
          getUsageSignatureFromSoftwareAndSharedPart(
              logger, cfg['software_root'], shared_root))
    if not os.path.exists(cfg['instance_root']):
      logger.debug(
          "Ignoring non existant instance root %s from %s",
          cfg['instance_root'],
          slapos_cfg,
      )
    else:
      signatures.update(
          getUsageSignaturesFromSubInstance(logger, cfg['instance_root'], visited))
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
  try:
    parser.read([path])
    cfg = {
      'software_root': parser.get('slapos', 'software_root'),
      'instance_root': parser.get('slapos', 'instance_root'),
      'shared_part_list': parser.get('slapos', 'shared_part_list').splitlines()
    }
  except configparser.Error:
    logger.debug('Ignored config at %s because of error', path, exc_info=True)
    return None
  logger.debug('Read config: %s', cfg)
  return cfg


def getUsageSignatureFromSoftwareAndSharedPart(
    logger, software_root, shared_root, ignored_shared_parts=()):
  """Look in all softwares and shared parts to collect the signatures
  that are used.
  `ignored_shared_parts` is useful during dry-run, we want to ignore
  already the parts that we are about to delete.
  """
  signatures = {}
  for installed_cfg in glob.glob(os.path.join(software_root, '*',
                                              '.installed.cfg')):
    with open(installed_cfg) as f:
      signatures[installed_cfg] = f.read()
  for script in glob.glob(os.path.join(software_root, '*', 'bin', '*')):
    with open(script) as f:
      try:
        signatures[script] = f.read()
      except UnicodeDecodeError:
        logger.debug("Skipping script %s that could not be decoded", script)
  if shared_root:
    for shared_part in glob.glob(os.path.join(shared_root, '*', '*')):
      if shared_part not in ignored_shared_parts:
        for x in os.listdir(shared_part):
          if x == '.buildout-shared.json' or \
             fnmatchcase(x, '.*signature'):
            x = os.path.join(shared_part, x)
            with open(x) as f:
              signatures[x] = f.read()
  return signatures
