##############################################################################
#
# Copyright (c) 2026 Nexedi SA and Contributors. All Rights Reserved.
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

import os
# importing slapos.testing.testcase reads these at import time
os.environ.setdefault('SLAPOS_TEST_IPV4', '127.0.0.1')
os.environ.setdefault('SLAPOS_TEST_IPV6', '::1')

import unittest

from slapos.testing import testcase


class TestServeSoftwareURL(unittest.TestCase):
  """_serveSoftwareURL rewrites a local Software Release path to the URL served
  by the slapos-sr-testing software-web-server, and requires that server."""

  _env_keys = ('SLAPOS_TEST_SOFTWARE_ROOT_URL', 'SLAPOS_TEST_SOFTWARE_ROOT_DIR')

  def setUp(self):
    self._saved = {k: os.environ.pop(k, None) for k in self._env_keys}

  def tearDown(self):
    for k, v in self._saved.items():
      if v is None:
        os.environ.pop(k, None)
      else:
        os.environ[k] = v

  def _serveFromCheckout(self):
    os.environ['SLAPOS_TEST_SOFTWARE_ROOT_URL'] = 'http://10.0.0.1:9080'
    os.environ['SLAPOS_TEST_SOFTWARE_ROOT_DIR'] = '/checkout'

  def test_remote_url_is_left_unchanged(self):
    self.assertEqual(
      testcase._serveSoftwareURL('https://lab/nexedi/slapos/software/a/software.cfg'),
      ('https://lab/nexedi/slapos/software/a/software.cfg', None))

  def test_local_path_is_rewritten_to_the_served_url(self):
    self._serveFromCheckout()
    self.assertEqual(
      testcase._serveSoftwareURL('/checkout/software/rapid-cdn/software.cfg'),
      ('http://10.0.0.1:9080/software/rapid-cdn/software.cfg', '/checkout'))

  def test_root_url_trailing_slash_is_not_doubled(self):
    os.environ['SLAPOS_TEST_SOFTWARE_ROOT_URL'] = 'http://10.0.0.1:9080/'
    os.environ['SLAPOS_TEST_SOFTWARE_ROOT_DIR'] = '/checkout'
    self.assertEqual(
      testcase._serveSoftwareURL('/checkout/software/a/software.cfg')[0],
      'http://10.0.0.1:9080/software/a/software.cfg')

  def test_path_outside_the_served_checkout_raises(self):
    self._serveFromCheckout()
    self.assertRaises(
      RuntimeError,
      testcase._serveSoftwareURL,
      '/elsewhere/software/a/software.cfg')

  def test_local_path_without_a_server_raises(self):
    self.assertRaises(
      RuntimeError,
      testcase._serveSoftwareURL,
      '/checkout/software/a/software.cfg')


if __name__ == '__main__':
  unittest.main()
