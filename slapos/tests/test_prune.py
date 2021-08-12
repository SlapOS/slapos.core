##############################################################################
#
# Copyright (c) 2010 Vifib SARL and Contributors. All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsibility of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# guarantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

import tempfile
import logging
import os
import shutil
import unittest
import slapos.client
import six

try:
  import mock
except ImportError:
  from unittest import mock

from slapos.cli.prune import do_prune


class TestPrune(unittest.TestCase):
  def setUp(self):
    self.logger = mock.create_autospec(logging.getLogger())
    self.base_directory = tempfile.mkdtemp()
    self.shared_part_root = os.path.join(self.base_directory, 'shared')
    self.software_root = os.path.join(self.base_directory, 'software')
    self.instance_root = os.path.join(self.base_directory, 'instance')

    for d in (self.shared_part_root, self.software_root, self.instance_root):
      os.mkdir(d)
    self.addCleanup(shutil.rmtree, self.base_directory)

    self.config = {
        'shared_part_list': self.shared_part_root,
        'software_root': self.software_root,
        'instance_root': self.instance_root,
    }

  def _createFakeSoftware(self, name, using='', software_root=None):
    software_path = os.path.join(software_root or self.software_root, name)
    os.mkdir(software_path)
    with open(os.path.join(software_path, '.installed.cfg'), 'w') as f:
      f.write("""[buildout]
      using = {}
      """.format(using))
    return software_path

  def _createSharedPart(self, name, using='', shared_part_root=None):
    shared_part_name = os.path.join(shared_part_root or self.shared_part_root, name)
    shared_part_with_version = os.path.join(shared_part_name, name)
    os.makedirs(shared_part_with_version)
    with open(os.path.join(shared_part_with_version,
                           '.slapos.recipe.cmmi.signature'), 'w') as f:
      f.write("""signature
      using = {}
      """.format(using))
    return shared_part_with_version

  def test_simple_not_used_share_part(self):
    not_used = self._createSharedPart('not_used')
    used = self._createSharedPart('used_part')
    self._createFakeSoftware(self.id(), using=used)
    do_prune(self.logger, self.config, False)
    self.assertTrue(os.path.exists(used))
    self.assertFalse(os.path.exists(not_used))
    self.logger.warning.assert_called_with(
        'Unused shared parts at %s%s', not_used, ' ... removed')

  def test_dry_run(self):
    not_used = self._createSharedPart('not_used')
    used = self._createSharedPart('used_part')
    self._createFakeSoftware(self.id(), using=used)
    do_prune(self.logger, self.config, True)
    self.assertTrue(os.path.exists(used))
    self.assertTrue(os.path.exists(not_used))
    self.logger.warning.assert_called_with(
        'Unused shared parts at %s%s', not_used, '')

  def test_shared_part_used_in_another_shared_part(self):
    not_used = self._createSharedPart('not_used')
    indirectly_used_part = self._createSharedPart('part_used_indirectly')
    directly_used_part = self._createSharedPart('directly_used_part', using=indirectly_used_part)
    self._createFakeSoftware(self.id(), using=directly_used_part)
    do_prune(self.logger, self.config, False)
    self.assertTrue(os.path.exists(indirectly_used_part))
    self.assertTrue(os.path.exists(directly_used_part))
    self.assertFalse(os.path.exists(not_used))
    self.logger.warning.assert_called_with(
        'Unused shared parts at %s%s', not_used, ' ... removed')

  def test_shared_part_not_used_recursive_dependencies(self):
    used_only_by_orphan_part = self._createSharedPart(
        'used_only_by_orphan_part')
    not_used = self._createSharedPart(
        'not_used', using=used_only_by_orphan_part)
    used_directly = self._createSharedPart('used_directly')

    self._createFakeSoftware(self.id(), using=used_directly)
    do_prune(self.logger, self.config, True)
    self.assertIn(
        mock.call('Unused shared parts at %s%s', not_used, ''),
        self.logger.warning.mock_calls)
    self.assertIn(
        mock.call(
            'Unused shared parts at %s%s', used_only_by_orphan_part, ''),
        self.logger.warning.mock_calls)
    do_prune(self.logger, self.config, False)
    self.assertTrue(os.path.exists(used_directly))
    self.assertFalse(os.path.exists(not_used))
    self.assertFalse(os.path.exists(used_only_by_orphan_part))

  def test_shared_part_used_in_buildout_script(self):
    not_used = self._createSharedPart('not_used')
    used_in_script = self._createSharedPart('used_in_script')
    fake_software_path = self._createFakeSoftware(self.id())
    os.mkdir(os.path.join(fake_software_path, 'bin'))
    script = os.path.join(fake_software_path, 'bin', 'buildout')
    with open(script, 'w') as f:
      f.write('#!{}'.format(used_in_script))
    # bin/ can also contain binary executables, this should not cause problems
    binary_script = os.path.join(fake_software_path, 'bin', 'binary')
    with open(binary_script, 'wb') as f:
      f.write(b'\x80')
    do_prune(self.logger, self.config, False)
    self.assertTrue(os.path.exists(used_in_script))
    self.assertFalse(os.path.exists(not_used))
    self.logger.warning.assert_called_with(
        'Unused shared parts at %s%s', not_used, ' ... removed')
    if six.PY3:
      self.logger.debug.assert_any_call(
        'Skipping script %s that could not be decoded', binary_script)


  def test_shared_part_used_in_recursive_instance(self):
    used_in_software_from_instance = self._createSharedPart('used_in_software_from_instance')
    used_in_shared_part_from_instance = self._createSharedPart('used_in_shared_part_from_instance')
    not_used = self._createSharedPart('not_used')

    # create instance
    instance = os.path.join(self.instance_root, 'slappart0')
    instance_etc = os.path.join(instance, 'etc')
    instance_software = os.path.join(instance, 'software')
    instance_instance = os.path.join(instance, 'instance')
    instance_shared_part_root = os.path.join(instance, 'shared')
    for p in instance_etc, instance_software, instance_instance, instance_shared_part_root:
      os.makedirs(p)
    instance_slapos_cfg = os.path.join(instance_etc, 'slapos.cfg')
    with open(instance_slapos_cfg, 'w') as f:
      f.write('''
[slapos]
software_root = {instance_software}
instance_root = {instance_instance}
shared_part_list =
  {self.shared_part_root}
  {instance_shared_part_root}
'''.format(**locals()))

    # install software and shared part in instance
    software_in_instance = self._createFakeSoftware(
        'soft_in_instance',
        using=used_in_software_from_instance,
        software_root=instance_software
    )
    shared_part_in_instance = self._createSharedPart(
        'shared_part_in_instance',
        using=used_in_shared_part_from_instance,
        shared_part_root=instance_shared_part_root
    )
    unused_shared_part_in_instance = self._createSharedPart(
        'unused_shared_part_in_instance',
        shared_part_root=instance_shared_part_root
    ) # could be pruned, but prune is not recursive.

    do_prune(self.logger, self.config, False)
    self.logger.debug.assert_any_call(
        'Reading config at %s', instance_slapos_cfg)

    self.assertTrue(os.path.exists(used_in_software_from_instance))
    self.assertTrue(os.path.exists(used_in_software_from_instance))
    self.assertTrue(os.path.exists(software_in_instance))
    self.assertTrue(os.path.exists(shared_part_in_instance))
    self.assertFalse(os.path.exists(not_used))

    self.logger.warning.assert_called_with(
        'Unused shared parts at %s%s', not_used, ' ... removed')

  def test_recursive_instance_broken_slapos_cfg(self):
    instance = os.path.join(self.instance_root, 'slappart0')
    instance_etc = os.path.join(instance, 'etc')
    os.makedirs(instance_etc)
    instance_slapos_cfg = os.path.join(instance_etc, 'slapos.cfg')

    # slapos.cfg might be not valid .ini file
    with open(instance_slapos_cfg, 'w') as f:
      f.write('this is not an actual slapos.cfg')
    do_prune(self.logger, self.config, False)
    self.logger.debug.assert_any_call(
        'Ignored config at %s because of error', instance_slapos_cfg, exc_info=True)

    # ... or an ini file without [slapos] section
    with open(instance_slapos_cfg, 'w') as f:
      f.write('[something]')
    do_prune(self.logger, self.config, False)
    self.logger.debug.assert_any_call(
        'Ignored config at %s because of error', instance_slapos_cfg, exc_info=True)

    # ... or referencing non existant paths
    with open(instance_slapos_cfg, 'w') as f:
      f.write('''
[slapos]
software_root = NOT EXIST SOFTWARE
instance_root = NOT EXIST INSTSTANCE
shared_part_list = NOT EXIST SHARED PART
''')
    do_prune(self.logger, self.config, False)
    self.assertIn(
        mock.call(
            'Ignoring non existant software root %s from %s',
            'NOT EXIST SOFTWARE',
            instance_slapos_cfg),
        self.logger.debug.mock_calls)
    self.assertIn(
        mock.call(
            'Ignoring non existant instance root %s from %s',
            'NOT EXIST INSTSTANCE',
            instance_slapos_cfg),
        self.logger.debug.mock_calls)

    self.assertIn(
        mock.call(
            'Ignoring non existant shared root %s from %s',
            'NOT EXIST SHARED PART',
            instance_slapos_cfg),
        self.logger.debug.mock_calls)

  def test_recursive_instance_broken_slapos_cfg_does_not_cause_instance_to_be_ignored(self):
    used_in_software_from_instance = self._createSharedPart('used_in_software_from_instance')

    instance = os.path.join(self.instance_root, 'slappart0')
    instance_software = os.path.join(instance, 'software')
    os.makedirs(instance_software)
    software_in_instance = self._createFakeSoftware(
        'soft_in_instance',
        using=used_in_software_from_instance,
        software_root=instance_software
    )

    # a broken slapos.cfg
    folder_containing_wrong_slapos_cfg = os.path.join(instance, 'aaa')
    os.makedirs(folder_containing_wrong_slapos_cfg)
    wrong_slapos_cfg = os.path.join(folder_containing_wrong_slapos_cfg, 'slapos.cfg')
    with open(wrong_slapos_cfg, 'w') as f:
      f.write("broken")

    # a "real" slapos.cfg
    instance_etc = os.path.join(instance, 'etc')
    os.makedirs(instance_etc)
    instance_slapos_cfg = os.path.join(instance_etc, 'slapos.cfg')
    with open(instance_slapos_cfg, 'w') as f:
      f.write('''
[slapos]
software_root = {instance_software}
instance_root = anything
shared_part_list = anything
'''.format(**locals()))

    do_prune(self.logger, self.config, False)
    self.assertTrue(os.path.exists(used_in_software_from_instance))

  def test_recursive_instance_multiple_levels(self):
    used_in_software_from_instance = self._createSharedPart('used_in_software_from_instance')

    instance_level1 = os.path.join(self.instance_root, 'slappart0')
    instance_level1_etc = os.path.join(instance_level1, 'etc')
    os.makedirs(instance_level1_etc)
    instance_level1_slapos_cfg = os.path.join(instance_level1_etc, 'slapos.cfg')
    with open(instance_level1_slapos_cfg, 'w') as f:
      f.write('''
[slapos]
software_root = anything
instance_root = {instance_level1}
shared_part_list = anything
'''.format(**locals()))

    instance_level2 = os.path.join(instance_level1, 'srv', 'runner')
    instance_level2_etc = os.path.join(instance_level2, 'etc')
    os.makedirs(instance_level2_etc)
    instance_level2_software = os.path.join(instance_level2, 'software')
    os.makedirs(instance_level2_software)
    software_in_instance = self._createFakeSoftware(
        'soft_in_instance_level2',
        using=used_in_software_from_instance,
        software_root=instance_level2_software
    )

    instance_level2_slapos_cfg = os.path.join(instance_level2_etc, 'slapos.cfg')
    with open(instance_level2_slapos_cfg, 'w') as f:
      f.write('''
[slapos]
software_root = {instance_level2_software}
instance_root = {instance_level2}
shared_part_list = anything
'''.format(**locals()))

    do_prune(self.logger, self.config, False)
    self.assertTrue(os.path.exists(used_in_software_from_instance))
