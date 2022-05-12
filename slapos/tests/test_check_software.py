##############################################################################
#
# Copyright (c) 2021 Vifib SARL and Contributors. All Rights Reserved.
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

from __future__ import absolute_import
import unittest
import mock
import os
import glob
import tempfile
import textwrap
import warnings

from slapos.testing.check_software import checkSoftware
from slapos.grid.utils import md5digest
from .test_standalone import SlapOSStandaloneTestCase


class TestCheckSoftwareLDD(SlapOSStandaloneTestCase):
  # BBB python2
  assertRaisesRegex = getattr(
      unittest.TestCase,
      'assertRaisesRegex',
      unittest.TestCase.assertRaisesRegexp,
  )

  def _get_zlib_environment(self, with_rpath=True):
    """returns an environment that will compile with slapos' zlib
    """
    # find a zlib in SLAPOS_TEST_SHARED_PART_LIST
    zlib_location = None
    for shared_part in self.standalone._shared_part_list:
      for zlib_location in glob.glob(os.path.join(shared_part, 'zlib', '*')):
        break
      if zlib_location:
        break
    assert zlib_location
    return {
        'CFLAGS':
            '-I{zlib_location}/include'.format(**locals()),
        'LDFLAGS':
            '-L{zlib_location}/lib -Wl,-rpath={zlib_location}/lib'.format(
                **locals()) if with_rpath else '-L{zlib_location}/lib'.format(
                    **locals())
    }

  def _install_software(self, environment, shared=True):
    environment_option = ''
    for k, v in environment.items():
      environment_option += '  {k}={v}\n'.format(k=k, v=v)

    shared_option = 'true' if shared else 'false'
    test_software_archive_url = os.path.join(
        os.path.dirname(__file__), 'data', 'cmmi', 'dist.tar.gz')
    with tempfile.NamedTemporaryFile(
        suffix="-%s.cfg" % self.id(),
        mode='w',
    ) as f:
      f.write(
          textwrap.dedent('''
              [buildout]
              parts = cmmi
              newest = false
              offline = true
              eggs-directory = {os.environ[SLAPOS_TEST_EGGS_DIRECTORY]}
              develop-eggs-directory = {os.environ[SLAPOS_TEST_DEVELOP_EGGS_DIRECTORY]}
 
              [cmmi]
              recipe = slapos.recipe.cmmi
              url = {test_software_archive_url}
              shared = {shared_option}
              environment =
              {environment_option}
      ''').format(os=os, **locals()))
      f.flush()
      self.standalone.supply(f.name)
      self.standalone.waitForSoftware()
      return f.name

  def test_software_using_system_libraries(self):
    software_url = self._install_software(
        self._get_zlib_environment(with_rpath=False), shared=False)
    with self.assertRaisesRegex(
        RuntimeError,
        './bin/slapos-core-test uses system library .*libz.so.* for libz.so',
    ):
      checkSoftware(self.standalone, software_url)

  def test_shared_part_using_system_libraries(self):
    software_url = self._install_software(
        self._get_zlib_environment(with_rpath=False))
    with self.assertRaisesRegex(
        RuntimeError,
        './bin/slapos-core-test uses system library .*libz.so.* for libz.so',
    ):
      checkSoftware(self.standalone, software_url)

  def test_shared_part_referencing_software(self):
    environment = self._get_zlib_environment()
    environment['reference-to-part'] = '${buildout:parts-directory}'
    software_url = self._install_software(environment=environment)
    with self.assertRaisesRegex(
        RuntimeError,
        'Shared part is referencing non shared part or software',
    ):
      checkSoftware(self.standalone, software_url)

  def test_ok(self):
    software_url = self._install_software(
        environment=self._get_zlib_environment())
    checkSoftware(self.standalone, software_url)

  def test_software_check_isolated(self):
    # if a software populated shared parts with wrong parts, this does not
    # impact checking other softwares, as long as they don't use the problematic
    # parts
    self.test_shared_part_using_system_libraries()
    self.test_ok()


class TestCheckSoftwareEggVulnerability(SlapOSStandaloneTestCase):

  def _install_software(self):
    """install a fake software with vulnerable packages, installed as
    eggs and develop-eggs, and for different python versions.
    """
    software_url = '/fake/path/software.cfg'
    software_hash = md5digest(software_url)
    self.standalone.supply(software_url)

    software_dir = os.path.join(
        self.standalone.software_directory,
        software_hash,
    )
    eggs_dir = os.path.join(software_dir, 'eggs')

    os.makedirs(os.path.join(eggs_dir, 'urllib3-1.22-py3.7.egg', 'EGG-INFO'))
    with open(
        os.path.join(
            eggs_dir,
            'urllib3-1.22-py3.7.egg',
            'EGG-INFO',
            'PKG-INFO',
        ), 'w') as f:
      f.write(
          textwrap.dedent('''\
              Metadata-Version: 2.1
              Name: urllib3
              Version: 1.22
              '''))

    develop_eggs_dir = os.path.join(software_dir, 'develop-eggs')
    os.makedirs(
        os.path.join(
            develop_eggs_dir,
            'lxml-4.6.3-py2.7-linux-x86_64.egg',
            'EGG-INFO',
        ))
    with open(
        os.path.join(
            develop_eggs_dir,
            'lxml-4.6.3-py2.7-linux-x86_64.egg',
            'EGG-INFO',
            'PKG-INFO',
        ), 'w') as f:
      f.write(
          textwrap.dedent('''\
              Metadata-Version: 2.1
              Name: lxml
              Version: 4.6.3
              '''))
    with open(os.path.join(software_dir, '.completed'), 'w') as f:
      f.write('Thu Dec  2 01:35:02 2021')
    with open(os.path.join(software_dir, '.installed.cfg'), 'w') as f:
      f.write('[buildout]')
    return software_url

  def test_egg_known_vulnerability(self):
    software_url = self._install_software()
    with warnings.catch_warnings(record=True) as warning_context:
      warnings.simplefilter("always")
      checkSoftware(self.standalone, software_url)

    warning, = [w for w in warning_context if 'vulnerable' in str(w.message)]
    self.assertIn(
        'urllib3 before version 1.23 does not remove the Authorization HTTP header when',
        str(warning.message),
    )
    self.assertIn(
        'Lxml 4.6.5 includes a fix for CVE-2021-43818',
        str(warning.message),
    )
