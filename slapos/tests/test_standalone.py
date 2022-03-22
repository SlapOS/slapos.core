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
import mock
import os
import tempfile
import textwrap
import hashlib
import socket
import errno
import time
import glob
import subprocess
import multiprocessing
from contextlib import closing
from six.moves.configparser import ConfigParser

import psutil

from slapos.slap.standalone import StandaloneSlapOS
from slapos.slap.standalone import SlapOSNodeSoftwareError
from slapos.slap.standalone import PartitionForwardConfiguration
from slapos.slap.standalone import PartitionForwardAsPartitionConfiguration
import slapos.util


SLAPOS_TEST_IPV4 = os.environ['SLAPOS_TEST_IPV4']
SLAPOS_TEST_IPV6 = os.environ['SLAPOS_TEST_IPV6']
SLAPOS_TEST_PORT = int(os.environ.get('SLAPOS_TEST_PORT', 33333))


def checkPortIsFree():
  """Sanity check that we did not leak a process listening on this port.
  """
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  with closing(s):
    try:
      s.connect((SLAPOS_TEST_IPV4, SLAPOS_TEST_PORT))
      raise RuntimeError(
          "Port needed for tests ({SLAPOS_TEST_IPV4}:{SLAPOS_TEST_PORT}) is already in use"
          .format(**globals()))
    except socket.error as e:
      if e.errno == errno.ECONNREFUSED:
        return
      raise


class TestSlapOSStandaloneSetup(unittest.TestCase):
  # BBB python2
  assertRaisesRegex = getattr(
      unittest.TestCase, 'assertRaisesRegex',
      unittest.TestCase.assertRaisesRegexp)

  def setUp(self):
    checkPortIsFree()

  def test_format(self):
    working_dir = tempfile.mkdtemp(prefix=__name__)
    self.addCleanup(slapos.util.rmtree, working_dir)
    standalone = StandaloneSlapOS(
        working_dir, SLAPOS_TEST_IPV4, SLAPOS_TEST_PORT)
    self.addCleanup(standalone.stop)
    standalone.format(3, SLAPOS_TEST_IPV4, SLAPOS_TEST_IPV6)

    self.assertTrue(os.path.exists(standalone.software_directory))
    self.assertTrue(os.path.exists(standalone.instance_directory))
    self.assertTrue(
        os.path.exists(
            os.path.join(standalone.instance_directory, 'slappart0')))
    self.assertTrue(
        os.path.exists(
            os.path.join(standalone.instance_directory, 'slappart1')))
    self.assertTrue(
        os.path.exists(
            os.path.join(standalone.instance_directory, 'slappart2')))

  def test_reformat_less_partitions(self):
    working_dir = tempfile.mkdtemp(prefix=__name__)
    self.addCleanup(slapos.util.rmtree, working_dir)
    standalone = StandaloneSlapOS(
        working_dir, SLAPOS_TEST_IPV4, SLAPOS_TEST_PORT)
    self.addCleanup(standalone.stop)
    standalone.format(2, SLAPOS_TEST_IPV4, SLAPOS_TEST_IPV6)
    standalone.format(1, SLAPOS_TEST_IPV4, SLAPOS_TEST_IPV6)
    self.assertFalse(
        os.path.exists(
            os.path.join(standalone.instance_directory, 'slappart1')))
    self.assertEqual(
        ['slappart0'],
        [cp.getId() for cp in standalone.computer.getComputerPartitionList()])

  def test_reformat_less_chmod_files(self):
    working_dir = tempfile.mkdtemp(prefix=__name__)
    self.addCleanup(slapos.util.rmtree, working_dir)
    standalone = StandaloneSlapOS(
        working_dir, SLAPOS_TEST_IPV4, SLAPOS_TEST_PORT)
    self.addCleanup(standalone.stop)
    standalone.format(2, SLAPOS_TEST_IPV4, SLAPOS_TEST_IPV6)
    # removing this directory should not be a problem
    chmoded_dir_path = os.path.join(standalone.instance_directory, 'slappart1', 'directory')
    os.mkdir(chmoded_dir_path)
    os.chmod(chmoded_dir_path, 0o000)
    standalone.format(1, SLAPOS_TEST_IPV4, SLAPOS_TEST_IPV6)
    self.assertFalse(os.path.exists(chmoded_dir_path))
    self.assertEqual(
        ['slappart0'],
        [cp.getId() for cp in standalone.computer.getComputerPartitionList()])

  def test_reformat_different_base_name(self):
    working_dir = tempfile.mkdtemp(prefix=__name__)
    self.addCleanup(slapos.util.rmtree, working_dir)
    standalone = StandaloneSlapOS(
        working_dir, SLAPOS_TEST_IPV4, SLAPOS_TEST_PORT)
    self.addCleanup(standalone.stop)
    standalone.format(
        1, SLAPOS_TEST_IPV4, SLAPOS_TEST_IPV6, partition_base_name="a")
    self.assertTrue(
        os.path.exists(os.path.join(standalone.instance_directory, 'a0')))
    standalone.format(
        1, SLAPOS_TEST_IPV4, SLAPOS_TEST_IPV6, partition_base_name="b")
    self.assertFalse(
        os.path.exists(os.path.join(standalone.instance_directory, 'a0')))
    self.assertTrue(
        os.path.exists(os.path.join(standalone.instance_directory, 'b0')))
    self.assertEqual(
        ['b0'],
        [cp.getId() for cp in standalone.computer.getComputerPartitionList()])

  def test_reformat_refuse_deleting_running_partition(self):
    working_dir = tempfile.mkdtemp(prefix=__name__)
    self.addCleanup(slapos.util.rmtree, working_dir)
    standalone = StandaloneSlapOS(
        working_dir, SLAPOS_TEST_IPV4, SLAPOS_TEST_PORT)
    self.addCleanup(standalone.stop)
    standalone.format(1, SLAPOS_TEST_IPV4, SLAPOS_TEST_IPV6)
    with mock.patch("slapos.slap.ComputerPartition.getState", return_value="busy"),\
       self.assertRaisesRegex(ValueError, "Cannot reformat to remove busy partition at .*slappart0"):
      standalone.format(0, SLAPOS_TEST_IPV4, SLAPOS_TEST_IPV6)

  def test_slapos_node_format(self):
    working_dir = tempfile.mkdtemp(prefix=__name__)
    self.addCleanup(slapos.util.rmtree, working_dir)
    standalone = StandaloneSlapOS(
        working_dir, SLAPOS_TEST_IPV4, SLAPOS_TEST_PORT)
    self.addCleanup(standalone.stop)
    self.assertTrue(os.path.exists(standalone.instance_directory))
    format_command = (standalone._slapos_wrapper, 'node', 'format', '--now')
    glob_pattern = os.path.join(standalone.instance_directory, 'slappart*')
    self.assertFalse(glob.glob(glob_pattern))
    self.assertTrue(subprocess.call(format_command))
    self.assertFalse(glob.glob(glob_pattern))
    for partition_count in (3, 2):
      standalone.format(partition_count, SLAPOS_TEST_IPV4, SLAPOS_TEST_IPV6)
      self.assertEqual(partition_count, len(glob.glob(glob_pattern)))
      subprocess.check_call(format_command)
      partitions = glob.glob(glob_pattern)
      self.assertEqual(partition_count, len(partitions))
      for path in partitions:
        slapos.util.rmtree(path)
      subprocess.check_call(format_command)
      self.assertEqual(partition_count, len(glob.glob(glob_pattern)))

  def test_two_instance_from_same_directory(self):
    working_dir = tempfile.mkdtemp(prefix=__name__)
    self.addCleanup(slapos.util.rmtree, working_dir)
    standalone1 = StandaloneSlapOS(
        working_dir, SLAPOS_TEST_IPV4, SLAPOS_TEST_PORT)

    def maybestop():
      # try to stop anyway, not to leak processes if test fail
      try:
        standalone1.stop()
      except:
        pass

    self.addCleanup(maybestop)

    # create another class instance, will control the same standanlone slapos.
    standalone2 = StandaloneSlapOS(
        working_dir, SLAPOS_TEST_IPV4, SLAPOS_TEST_PORT)
    standalone2.stop()

    # stopping standalone2 stops everything
    with self.assertRaises(BaseException):
      standalone1.supply("https://example.com/software.cfg")
    with self.assertRaises(BaseException):
      standalone1.stop()

  def test_partition_forward(self):
    # type: () -> None
    working_dir = tempfile.mkdtemp(prefix=__name__)
    self.addCleanup(slapos.util.rmtree, working_dir)
    partition_forward_config = [
        PartitionForwardConfiguration(
            'https://slapos1.example.com',
            'path/to/cert',
            'path/to/key',
            software_release_list=('https://example.com/software-1.cfg', ),
        ),
        PartitionForwardConfiguration(
            'https://slapos2.example.com',
            software_release_list=('https://example.com/software-2.cfg', ),
        ),
        PartitionForwardAsPartitionConfiguration(
            'https://slapos3.example.com',
            'computer',
            'partition',
            'path/to/cert',
            'path/to/key',
            software_release_list=('https://example.com/software-3.cfg', ),
        ),
        PartitionForwardAsPartitionConfiguration(
            'https://slapos4.example.com',
            'computer',
            'partition',
            software_release_list=('https://example.com/software-4.cfg', ),
        ),
    ]
    standalone = StandaloneSlapOS(
        working_dir,
        SLAPOS_TEST_IPV4,
        SLAPOS_TEST_PORT,
        partition_forward_configuration=partition_forward_config,
    )
    self.addCleanup(standalone.stop)

    config_parser = ConfigParser()
    config_parser.read([os.path.join(working_dir, 'etc', 'slapos.cfg')])
    self.assertTrue(
        config_parser.has_section('multimaster/https://slapos1.example.com'))
    self.assertEqual(
        'path/to/cert',
        config_parser.get('multimaster/https://slapos1.example.com', 'cert'))
    self.assertEqual(
        'path/to/key',
        config_parser.get('multimaster/https://slapos1.example.com', 'key'))
    self.assertEqual(
        'https://example.com/software-1.cfg',
        config_parser.get(
            'multimaster/https://slapos1.example.com',
            'software_release_list').strip())
    self.assertFalse(
        config_parser.has_option(
            'multimaster/https://slapos2.example.com', 'computer'))
    self.assertFalse(
        config_parser.has_option(
            'multimaster/https://slapos2.example.com', 'partition'))

    self.assertTrue(
        config_parser.has_section('multimaster/https://slapos2.example.com'))
    self.assertFalse(
        config_parser.has_option(
            'multimaster/https://slapos2.example.com', 'cert'))
    self.assertFalse(
        config_parser.has_option(
            'multimaster/https://slapos2.example.com', 'key'))

    self.assertTrue(
        config_parser.has_section('multimaster/https://slapos3.example.com'))
    self.assertEqual(
        'computer',
        config_parser.get(
            'multimaster/https://slapos3.example.com', 'computer'))
    self.assertEqual(
        'partition',
        config_parser.get(
            'multimaster/https://slapos3.example.com', 'partition'))

    self.assertTrue(
        config_parser.has_section('multimaster/https://slapos4.example.com'))


class SlapOSStandaloneTestCase(unittest.TestCase):
  # This test case takes care of stopping the standalone instance
  # in a cleanup, but subclasses who needs to control shutdown
  # can set this class attribute to False to prevent this behavior.
  _auto_stop_standalone = True

  def setUp(self):
    checkPortIsFree()
    working_dir = tempfile.mkdtemp(prefix=__name__)
    self.addCleanup(slapos.util.rmtree, working_dir)
    self.standalone = StandaloneSlapOS(
        working_dir,
        SLAPOS_TEST_IPV4,
        SLAPOS_TEST_PORT,
        shared_part_list=[
            os.path.expanduser(p) for p in os.environ.get(
                'SLAPOS_TEST_SHARED_PART_LIST', '').split(os.pathsep) if p
        ],
    )
    if self._auto_stop_standalone:
      self.addCleanup(self.standalone.stop)
    self.standalone.format(1, SLAPOS_TEST_IPV4, SLAPOS_TEST_IPV6)


class TestSlapOSStandaloneLogFile(SlapOSStandaloneTestCase):
  def test_log_files(self):
    log_directory = self.standalone._log_directory
    with open(os.path.join(log_directory, 'slapos-proxy.log')) as f:
      self.assertIn("Running on http", f.read())

    self.standalone.waitForSoftware()
    with open(os.path.join(log_directory, 'slapos-node-software.log')) as f:
      self.assertIn("Processing software releases", f.read())

    self.standalone.waitForInstance()
    with open(os.path.join(log_directory, 'slapos-node-instance.log')) as f:
      self.assertIn("Processing computer partitions", f.read())

    self.standalone.waitForReport()
    with open(os.path.join(log_directory, 'slapos-node-report.log')) as f:
      self.assertIn("Aggregating and sending usage reports", f.read())

    self.assertTrue(
        os.path.exists(
            os.path.join(log_directory, 'slapos-instance-supervisord.log')))


class TestSlapOSStandaloneSoftware(SlapOSStandaloneTestCase):
  def test_install_software(self):
    with tempfile.NamedTemporaryFile(suffix="-%s.cfg" % self.id()) as f:
      f.write(
          textwrap.dedent(
              '''
              [buildout]
              parts = instance
              newest = false
              [instance]
              recipe = plone.recipe.command==1.1
              command = touch ${buildout:directory}/instance.cfg
              update-command = touch ${buildout:directory}/updated
      ''').encode())
      f.flush()
      self.standalone.supply(f.name)
      self.standalone.waitForSoftware()

      software_hash = hashlib.md5(f.name.encode()).hexdigest()
      software_installation_path = os.path.join(
          self.standalone.software_directory, software_hash)
      self.assertTrue(os.path.exists(software_installation_path))
      self.assertTrue(
          os.path.exists(os.path.join(software_installation_path, 'bin')))
      self.assertTrue(
          os.path.exists(os.path.join(software_installation_path, 'parts')))
      self.assertTrue(
          os.path.exists(
              os.path.join(software_installation_path, '.completed')))
      self.assertTrue(
          os.path.exists(
              os.path.join(software_installation_path, 'instance.cfg')))

      # install respect the .completed file, once software is installed,
      # waitForSoftware will not process again software
      self.standalone.waitForSoftware()
      self.assertFalse(
          os.path.exists(
              os.path.join(software_installation_path, 'updated')))

      # waitForSoftware has a way to "force" reinstalling all software
      self.standalone.waitForSoftware(install_all=True)
      self.assertTrue(
          os.path.exists(
              os.path.join(software_installation_path, 'updated')))

      # destroy
      self.standalone.supply(f.name, state='destroyed')
      self.standalone.waitForSoftware()
      self.assertFalse(os.path.exists(software_installation_path))

  def test_install_software_failure(self):
    with tempfile.NamedTemporaryFile(suffix="-%s.cfg" % self.id()) as f:
      f.write(
          textwrap.dedent(
              '''
              [buildout]
              parts = error
              newest = false
              [error]
              recipe = plone.recipe.command==1.1
              command = bash -c "exit 123"
              stop-on-error = true
      ''').encode())
      f.flush()
      self.standalone.supply(f.name)

      with self.assertRaises(SlapOSNodeSoftwareError) as e:
        self.standalone.waitForSoftware()

      self.assertEqual(1, e.exception.args[0]['exitstatus'])
      self.assertIn(
          "Error: Non zero exit code (123) while running command.",
          e.exception.args[0]['output'])
      # SlapOSNodeSoftwareError.__str__ also displays output nicely
      self.assertIn(
          "SlapOSNodeSoftwareError exitstatus: 1 output:", str(e.exception))
      self.assertIn(
          "Error: Non zero exit code (123) while running command.",
          str(e.exception))
      self.assertNotIn(r"\n", str(e.exception))

  def test_install_software_failure_log_with_ansi_codes(self):
    with tempfile.NamedTemporaryFile(suffix="-%s.cfg" % self.id()) as f:
      f.write(
          textwrap.dedent(
              r'''
              [buildout]
              parts = error
              newest = false
              [error]
              recipe = plone.recipe.command==1.1
              command = bash -c "echo -e '\033[0;31mRed\033[0m \033[0;32mGreen\033[0m \033[0;34mBlue\033[0m' ; exit 123"
              stop-on-error = true
      ''').encode())
      f.flush()
      self.standalone.supply(f.name)

      with self.assertRaises(SlapOSNodeSoftwareError) as e:
        self.standalone.waitForSoftware()

      self.assertEqual(1, e.exception.args[0]['exitstatus'])
      self.assertIn("Red Green Blue", e.exception.args[0]['output'])


class TestSlapOSStandaloneInstance(SlapOSStandaloneTestCase):
  _auto_stop_standalone = False  # we stop explicitly

  def test_request_instance(self):
    with tempfile.NamedTemporaryFile(suffix="-%s.cfg" % self.id()) as f:
      # This is a minimal / super fast buildout that's compatible with slapos.
      # We don't want to install slapos.cookbook because installation takes too
      # much time, so we use simple plone.recipe.command and shell.
      # This buildout create an instance with two parts:
      #  check_parameter: that checks that the requested parameter is set
      #  publish: that publish some parameters so that we can assert it's published.
      software_url = f.name
      f.write(
          textwrap.dedent(
              '''
              [buildout]
              parts = instance
              newest = false

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
    self.assertEqual({'published': 'parameter'},
                     partition.getConnectionParameterDict())

    # check instance files
    parition_directory = os.path.join(
        self.standalone.instance_directory, 'slappart0')
    self.assertTrue(
        os.path.exists(os.path.join(parition_directory, '.installed.cfg')))
    self.assertTrue(
        os.path.exists(os.path.join(parition_directory, 'instance.check')))

    # check instance supervisor, there should be only watchdog now
    with self.standalone.instance_supervisor_rpc as instance_supervisor_rpc:
      self.assertEqual(
          ['watchdog'],
          [p['name'] for p in instance_supervisor_rpc.getAllProcessInfo()])

    # delete instance
    self.standalone.request(
        software_url,
        'default',
        'instance',
        partition_parameter_kw={'partition': 'parameter'},
        state='destroyed',
    )
    self.standalone.waitForInstance()
    # instantiate does nothing, it will be deleted with `report`
    self.assertTrue(
        os.path.exists(os.path.join(parition_directory, 'instance.check')))
    self.standalone.waitForReport()
    self.assertFalse(
        os.path.exists(os.path.join(parition_directory, 'instance.check')))

    # check that stopping leaves no process
    process_list = []
    with self.standalone.instance_supervisor_rpc as instance_supervisor_rpc:
      process_list.append(psutil.Process(instance_supervisor_rpc.getPID()))
      process_list.extend([
          psutil.Process(p['pid'])
          for p in instance_supervisor_rpc.getAllProcessInfo()
          if p['statename'] == 'RUNNING'
      ])
    with self.standalone.system_supervisor_rpc as system_supervisor_rpc:
      process_list.append(psutil.Process(system_supervisor_rpc.getPID()))
      process_list.extend([
          psutil.Process(p['pid'])
          for p in system_supervisor_rpc.getAllProcessInfo()
          if p['statename'] == 'RUNNING'
      ])
    self.assertEqual(set([True]), set([p.is_running() for p in process_list]))
    self.standalone.stop()
    self.assertEqual(set([False]), set([p.is_running() for p in process_list]))
