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
      s.connect((SLAPOS_TEST_IPV4, SLAPOS_TEST_PORT))
      raise RuntimeError("Port needed for tests is already in use")
    except socket.error as e:
      if e.errno == errno.ECONNREFUSED:
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


  def test_two_instance_from_same_directory(self):
    working_dir = tempfile.mkdtemp(prefix=__name__)
    self.addCleanup(shutil.rmtree, working_dir)
    standalone1 = StandaloneSlapOS(
      working_dir,
      SLAPOS_TEST_IPV4,
      SLAPOS_TEST_PORT
    )
    self.addCleanup(standalone1.shutdown)
    standalone2 = StandaloneSlapOS(
      working_dir,
      SLAPOS_TEST_IPV4,
      SLAPOS_TEST_PORT
    )


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


class TestSlapOSStandaloneSoftware(SlapOSStandaloneTestCase):

  def test_install_software(self):
    with tempfile.NamedTemporaryFile(suffix="-%s.cfg" % self.id()) as f:
      f.write(textwrap.dedent('''
        [buildout]
        parts = instance
        [instance]
        recipe = plone.recipe.command==1.1
        command = touch ${buildout:directory}/instance.cfg
      ''').encode())
      f.flush()
      self.standalone.supply(f.name)
      self.standalone.waitForSoftware()

      software_hash = hashlib.md5(f.name.encode()).hexdigest()
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
      self.standalone.waitForSoftware()
      self.assertFalse(os.path.exists(software_installation_path))

  def test_install_software_failure(self):
    with tempfile.NamedTemporaryFile(suffix="-%s.cfg" % self.id()) as f:
      f.write(textwrap.dedent('''
        [buildout]
        parts = error
        [error]
        recipe = plone.recipe.command==1.1
        command = bash -c "exit 123"
        stop-on-error = true
      ''').encode())
      f.flush()
      self.standalone.supply(f.name)

      with self.assertRaises(SlapOSNodeCommandError) as e:
        self.standalone.waitForSoftware()

      self.assertEqual(1, e.exception.args[0]['exitstatus'])
      self.assertIn(
        "Error: Non zero exit code (123) while running command.",
        e.exception.args[0]['output'])



class TestSlapOSStandaloneInstance(SlapOSStandaloneTestCase):

  def test_request_instance(self):
    with tempfile.NamedTemporaryFile(suffix="-%s.cfg" % self.id()) as f:
      # This is a minimal / super fast buildout that's compatible with slapos.
      # We don't want to install slapos.cookbook because installation takes too
      # much time, so we use simple plone.recipe.command and shell.
      # This buildout create an instance with two parts:
      #  check_parameter: that checks that the requested parameter is set
      #  publish: that publish some parameters so that we can assert it's published.
      software_url = f.name
      f.write(textwrap.dedent('''
        [buildout]
        parts = instance

        [instance]
        recipe = plone.recipe.command==1.1
        stop-on-error = true
        # we use @@DOLLAR@@{section:option} for what will become instance substitutions
        command = sed -e s/@@DOLLAR@@/$/g <<EOF > ${buildout:directory}/instance.cfg
          [buildout]
          parts = check_parameter publish
          eggs-directory = ${buildout:eggs-directory}

          [check_parameter]
          # check we were requested with request=parameter ( as a way to test
          # request parameters are sent )
          recipe = plone.recipe.command==1.1
          stop-on-error = true
          command = \\
            curl '@@DOLLAR@@{slap-connection:server-url}/registerComputerPartition?computer_reference=@@DOLLAR@@{slap-connection:computer-id}&computer_partition_reference=@@DOLLAR@@{slap-connection:partition-id}' \\
            | grep '<string>request</string><string>parameter</string>'

          [publish]
          # touch a file to check instance exists and publish a hardcoded parameter
          recipe = plone.recipe.command==1.1
          stop-on-error = true
          command = \\
            touch instance.check \\
              && curl -X POST @@DOLLAR@@{slap-connection:server-url}/setComputerPartitionConnectionXml \\
              -d computer_id=@@DOLLAR@@{slap-connection:computer-id} \\
              -d computer_partition_id=@@DOLLAR@@{slap-connection:partition-id} \\
              -d connection_xml='<dictionary><string>published</string><string>parameter</string></dictionary>'
          EOF
      ''').encode())
      f.flush()

      self.standalone.supply(software_url)
      self.standalone.waitForSoftware()

    self.standalone.request(
        software_url,
        'default',
        'instance',
        partition_parameter_kw={'request': 'parameter'})
    self.standalone.waitForInstance()

    # check published parameters
    partition = self.standalone.request(
        software_url,
        'default',
        'instance',
        partition_parameter_kw={'request': 'parameter'})
    self.assertEqual(
        {'published': 'parameter'},
        partition.getConnectionParameterDict()
    )

    # check instance files
    parition_directory = os.path.join(self.standalone.instance_directory, 'slappart0')
    self.assertTrue(os.path.exists(os.path.join(parition_directory, '.installed.cfg')))
    self.assertTrue(os.path.exists(os.path.join(parition_directory, 'instance.check')))

    # delete instance
    self.standalone.request(
        software_url,
        'default',
        'instance',
        partition_parameter_kw={'partition': 'parameter'},
        state='destroyed',
    )
    self.standalone.waitForInstance()
    # instanciate does nothing, it will be deleted with `report`
    self.assertTrue(os.path.exists(os.path.join(parition_directory, 'instance.check')))
    self.standalone.waitForReport()
    self.assertFalse(os.path.exists(os.path.join(parition_directory, 'instance.check')))
