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
import functools
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

  def _install_software(self, environment, shared=True, software_url=None, install_all=False):
    environment_option = ''
    for k, v in environment.items():
      environment_option += '  {k}={v}\n'.format(k=k, v=v)

    shared_option = 'true' if shared else 'false'
    test_software_archive_url = os.path.join(
        os.path.dirname(__file__), 'data', 'cmmi', 'dist.tar.gz')
    if software_url:
      software_file = open(software_url, 'w')
    else:
      software_file = tempfile.NamedTemporaryFile(
        suffix="-%s.cfg" % self.id(),
        mode='w',
      )
    with software_file as f:
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
      self.standalone.waitForSoftware(install_all=install_all)
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
    # parts.
    # For this test, we reuse the tests installing problematic software and
    # then the test installing a correct software, using the same software URL.
    # This way, we cover testing the case where a software is updated in place.
    with tempfile.NamedTemporaryFile(suffix="-%s.cfg" % self.id()) as software_url_file:
      software_url = software_url_file.name
      self._install_software = functools.partial(
        self._install_software, software_url=software_url, install_all=True)

      self.test_shared_part_using_system_libraries()
      self.test_shared_part_referencing_software()
      self.test_ok()
