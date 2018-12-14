##############################################################################
#
# Copyright (c) 2018 Vifib SARL and Contributors. All Rights Reserved.
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

import unittest
import os
import tempfile
import textwrap
import shutil
import hashlib
import socket
import errno
from contextlib import closing

import psutil

from slapos.slap.standalone import StandaloneSlapOS
from slapos.slap.standalone import SlapOSNodeCommandError

SLAPOS_TEST_WORKING_DIR = os.environ['SLAPOS_TEST_WORKING_DIR']
SLAPOS_TEST_IPV4 = os.environ['SLAPOS_TEST_IPV4']
SLAPOS_TEST_IPV6 = os.environ['SLAPOS_TEST_IPV6']
SLAPOS_TEST_PORT = int(os.environ['SLAPOS_TEST_PORT'])


def checkPortIsFree():
  """Sanity check that we did not leak a process listening on this port.
  """
  with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
    try:
      s.bind((SLAPOS_TEST_IPV4, SLAPOS_TEST_PORT))
    except socket.error as e:
      if e.errno == errno.EADDRINUSE:
        return
      raise


class TestSlapOSStandaloneSetup(unittest.TestCase):
  def setUp(self):
    checkPortIsFree()

  def test_format(self):
    working_dir = tempfile.mkdtemp(prefix=__name__)
    self.addCleanup(shutil.rmtree, working_dir)
    standalone = StandaloneSlapOS(
      working_dir,
      SLAPOS_TEST_IPV4,
      SLAPOS_TEST_PORT
    )
    self.addCleanup(standalone.shutdown)
    standalone.format(3, SLAPOS_TEST_IPV4, SLAPOS_TEST_IPV6)

    self.assertTrue(os.path.exists(standalone.software_directory))
    self.assertTrue(os.path.exists(standalone.instance_directory))
    self.assertTrue(os.path.exists(
      os.path.join(standalone.instance_directory, 'slappart0')))
    self.assertTrue(os.path.exists(
      os.path.join(standalone.instance_directory, 'slappart1')))
    self.assertTrue(os.path.exists(
      os.path.join(standalone.instance_directory, 'slappart2')))


class SlapOSStandaloneTestCase(unittest.TestCase):
  def setUp(self):
    checkPortIsFree()
    working_dir = tempfile.mkdtemp(prefix=__name__)
    self.addCleanup(shutil.rmtree, working_dir)
    self.standalone = StandaloneSlapOS(
      working_dir,
      SLAPOS_TEST_IPV4,
      SLAPOS_TEST_PORT
    )
    self.addCleanup(self.standalone.shutdown)

    self.standalone.format(1, SLAPOS_TEST_IPV4, SLAPOS_TEST_IPV6)


class TestSlapOSStandaloneInstall(SlapOSStandaloneTestCase):

  def test_install_software(self):
    with tempfile.NamedTemporaryFile(suffix="-%s.cfg" % self.id()) as f:
      f.write(textwrap.dedent('''
        [buildout]
        parts = p
        [p]
        recipe = plone.recipe.command
        command = touch ${buildout:directory}/instance.cfg
      '''))
      f.flush()
      self.standalone.supply(f.name)
      self.standalone.installSoftware()

      software_hash = hashlib.md5(f.name).hexdigest()
      software_installation_path = os.path.join(
        self.standalone.software_directory,
        software_hash
      )
      self.assertTrue(os.path.exists(software_installation_path))
      self.assertTrue(os.path.exists(
        os.path.join(software_installation_path, 'bin')))
      self.assertTrue(os.path.exists(
        os.path.join(software_installation_path, 'parts')))
      self.assertTrue(os.path.exists(
        os.path.join(software_installation_path, '.completed')))
      self.assertTrue(os.path.exists(
        os.path.join(software_installation_path, 'instance.cfg')))

      # destroy
      self.standalone.supply(f.name, state='destroyed')
      self.standalone.installSoftware()
      self.assertFalse(os.path.exists(software_installation_path))

  def test_install_software_failure(self):
    with tempfile.NamedTemporaryFile(suffix="-%s.cfg" % self.id()) as f:
      f.write(textwrap.dedent('''
        [buildout]
        parts = p
        [p]
        recipe = plone.recipe.command
        command = bash -c "exit 123"
        stop-on-error = true
      '''))
      f.flush()
      self.standalone.supply(f.name)

      with self.assertRaises(SlapOSNodeCommandError) as e:
        self.standalone.installSoftware()

      self.assertEqual(1, e.exception[0]['exitstatus'])
      self.assertIn(
        "Error: Non zero exit code (123) while running command.",
        e.exception[0]['output'])
