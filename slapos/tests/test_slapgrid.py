##############################################################################
# coding: utf-8
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

from __future__ import absolute_import
import logging
import os
import random
import shutil
import signal
import socket
import subprocess
import sys
import stat
import tempfile
import textwrap
import time
import unittest
import six
import pwd
from six.moves.urllib import parse
import json
import re
import grp
import hashlib
import errno

if six.PY2:
  # BBB python2
  unittest.TestCase.assertRaisesRegex = unittest.TestCase.assertRaisesRegexp
  unittest.TestCase.assertRegex = unittest.TestCase.assertRegexpMatches

import mock
from mock import patch
from zope.interface import implementer

import slapos.slap.slap
import slapos.grid.utils
import slapos.grid.svcbackend
from slapos.grid import slapgrid
from slapos.grid.utils import md5digest
from slapos.grid.watchdog import Watchdog
from slapos.grid import SlapObject
from slapos.grid.SlapObject import WATCHDOG_MARK
from slapos.manager.interface import IManager
from slapos.slap.slap import COMPUTER_PARTITION_REQUEST_LIST_TEMPLATE_FILENAME
from slapos.slap.exception import ConnectionError
import slapos.grid.SlapObject
from slapos import manager as slapmanager
from slapos.util import dumps

from slapos import __path__ as slapos_path
from zope import __path__ as zope_path

PROMISE_PATHS = sorted(set(map(os.path.dirname, list(slapos_path) + list(zope_path))))

import httmock


dummylogger = logging.getLogger()


WATCHDOG_TEMPLATE = """#!{python_path}
import sys
sys.path={sys_path}
import slapos.slap
import slapos.grid.watchdog

def bang(self_partition, message):
  nl = chr(10)
  with open('{watchdog_banged}', 'w') as fout:
    for key, value in vars(self_partition).items():
      fout.write('%s: %s%s' % (key, value, nl))
      if key == '_connection_helper':
        for k, v in vars(value).items():
          fout.write('   %s: %s%s' % (k, v, nl))
    fout.write(message)

slapos.slap.ComputerPartition.bang = bang
slapos.grid.watchdog.main()
"""

WRAPPER_CONTENT = """#!/bin/sh
touch worked &&
mkdir -p etc/run &&
echo "#!/bin/sh" > etc/run/wrapper &&
echo "while true; do echo Working; sleep 0.1; done" >> etc/run/wrapper &&
chmod 755 etc/run/wrapper
"""

DAEMON_CONTENT = """#!/bin/sh
mkdir -p etc/service &&
echo "#!/bin/sh" > etc/service/daemon &&
echo "sleep 1; touch launched
if [ -f ./crashed ]; then
while true; do echo Working; sleep 0.05; done
else
touch ./crashed; echo Failing; sleep 1; exit 111;
fi" >> etc/service/daemon &&
chmod 755 etc/service/daemon &&
touch worked
"""

PROMISE_CONTENT_TEMPLATE = """
# coding: utf-8
import sys
sys.path[0:0] = %(paths)r

from zope.interface import implementer
from slapos.grid.promise import interface
from slapos.grid.promise import GenericPromise

@implementer(interface.IPromise)
class RunPromise(GenericPromise):

  def __init__(self, config):
    super(RunPromise, self).__init__(config)
    self.setPeriodicity(minute=%(periodicity)r)
 
  def sense(self):
    %(content)s
 
    if not %(success)s:
      self.logger.error("failed")
    else:
      self.logger.info("success")

  def anomaly(self):
    return self._anomaly(result_count=2, failure_amount=%(failure_amount)r)

  def test(self):
    return self._test(result_count=1, failure_amount=%(failure_amount)r)
"""

class BasicMixin(object):
  def setUp(self):
    self._tempdir = tempfile.mkdtemp()
    self.manager_list = []
    self.software_root = os.path.join(self._tempdir, 'software')
    self.shared_parts_root = os.path.join(self._tempdir, 'shared')
    self.instance_root = os.path.join(self._tempdir, 'instance')
    if 'SLAPGRID_INSTANCE_ROOT' in os.environ:
      del os.environ['SLAPGRID_INSTANCE_ROOT']
    logging.basicConfig(level=logging.DEBUG)
    self.setSlapgrid()
    self.setMock()

  def getTestComputerClass(self):
    return ComputerForTest

  def setMock(self):
    module = slapos.grid.SlapObject
    func = 'getPythonExecutableFromSoftwarePath'
    orig = getattr(module, func)
    self.addCleanup(setattr, module, func, orig)
    setattr(module, func, lambda software_path: None)

  def setSlapgrid(self, develop=False, force_stop=False):
    if getattr(self, 'master_url', None) is None:
      self.master_url = 'http://127.0.0.1:80/'
    self.computer_id = 'computer'
    self.supervisord_socket = os.path.join(self._tempdir, 'sv.sock')
    self.supervisord_configuration_path = os.path.join(self._tempdir,
                                                       'supervisord')
    self.usage_report_periodicity = 1
    self.buildout = None
    self.certificate_repository_path = os.path.join(self._tempdir, 'partition_pki');
    if not os.path.isdir(self.certificate_repository_path):
      os.mkdir(self.certificate_repository_path)
    self.grid = slapgrid.Slapgrid(self.software_root,
                                  self.instance_root,
                                  self.master_url,
                                  self.computer_id,
                                  self.buildout,
                                  develop=develop,
                                  logger=logging.getLogger(),
                                  shared_part_list=self.shared_parts_root,
                                  force_stop=force_stop,
                                  certificate_repository_path=self.certificate_repository_path)
    self.grid._manager_list = self.manager_list
    # monkey patch buildout bootstrap

    def dummy(*args, **kw):
      pass

    slapos.grid.utils.bootstrapBuildout = dummy

    SlapObject.PROGRAM_PARTITION_TEMPLATE = textwrap.dedent("""\
        [program:%(program_id)s]
        directory=%(program_directory)s
        command=%(program_command)s
        process_name=%(program_name)s
        autostart=false
        autorestart=false
        startsecs=0
        startretries=0
        exitcodes=0
        stopsignal=TERM
        stopwaitsecs=60
        stopasgroup=true
        killasgroup=true
        user=%(user_id)s
        group=%(group_id)s
        serverurl=AUTO
        redirect_stderr=true
        stdout_logfile=%(instance_path)s/.%(program_id)s.log
        stderr_logfile=%(instance_path)s/.%(program_id)s.log
        environment=USER="%(USER)s",LOGNAME="%(USER)s",HOME="%(HOME)s"
        """)

  def launchSlapgrid(self, develop=False, force_stop=False):
    self.setSlapgrid(develop=develop, force_stop=force_stop)
    return self.grid.processComputerPartitionList()

  def launchSlapgridSoftware(self, develop=False, garbage_collection=False):
    self.setSlapgrid(develop=develop)
    return self.grid.processSoftwareReleaseList(garbage_collection=garbage_collection)

  def assertLogContent(self, log_path, expected, tries=600):
    for i in range(tries):
      with open(log_path) as f:
        if expected in f.read():
          return
      time.sleep(0.1)
    self.fail('%r not found in %s' % (expected, log_path))

  def assertIsCreated(self, path, tries=600):
    for i in range(tries):
      if os.path.exists(path):
        return
      time.sleep(0.1)
    self.fail('%s should be created' % path)

  def assertIsNotCreated(self, path, tries=50):
    for i in range(tries):
      if os.path.exists(path):
        self.fail('%s should not be created' % path)
      time.sleep(0.01)

  def assertInstanceDirectoryListEqual(self, instance_list):
    instance_list.append('etc')
    instance_list.append('var')
    instance_list.append('sv.sock')
    six.assertCountEqual(self, os.listdir(self.instance_root), instance_list)

  def tearDown(self):
    # XXX: Hardcoded pid, as it is not configurable in slapos
    svc = os.path.join(self.instance_root, 'var', 'run', 'supervisord.pid')
    if os.path.exists(svc):
      try:
        with open(svc) as f:
          pid = int(f.read().strip())
      except ValueError:
        pass
      else:
        os.kill(pid, signal.SIGTERM)
    shutil.rmtree(self._tempdir, True)


class TestRequiredOnlyPartitions(unittest.TestCase):
  def test_no_errors(self):
    required = ['one', 'three']
    existing = ['one', 'two', 'three']
    slapgrid.check_required_only_partitions(existing, required)

  def test_one_missing(self):
    required = ['foobar', 'two', 'one']
    existing = ['one', 'two', 'three']
    self.assertRaisesRegex(ValueError,
                            'Unknown partition: foobar',
                            slapgrid.check_required_only_partitions,
                            existing, required)

  def test_several_missing(self):
    required = ['foobar', 'barbaz']
    existing = ['one', 'two', 'three']
    self.assertRaisesRegex(ValueError,
                            'Unknown partitions: barbaz, foobar',
                            slapgrid.check_required_only_partitions,
                            existing, required)


class TestBasicSlapgridCP(BasicMixin, unittest.TestCase):
  def test_no_software_root(self):
    self.assertRaises(OSError, self.grid.processComputerPartitionList)

  def test_no_instance_root(self):
    os.mkdir(self.software_root)
    self.assertRaises(OSError, self.grid.processComputerPartitionList)

  def test_no_master(self):
    os.mkdir(self.software_root)
    os.mkdir(self.instance_root)
    self.assertEqual(
      self.grid.processComputerPartitionList(),
      slapgrid.SLAPGRID_OFFLINE_SUCCESS)

  def test_environment_variable_HOME(self):
    # When running instance, $HOME is set to the partition path
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    partition = computer.instance_list[0]
    partition.requested_state = 'started'
    partition.software.setBuildout('#!/bin/sh\n echo $HOME > env_HOME')
    with httmock.HTTMock(computer.request_handler):
      self.assertEqual(self.grid.processComputerPartitionList(), slapgrid.SLAPGRID_SUCCESS)
    with open(os.path.join(partition.partition_path, 'env_HOME')) as f:
      self.assertEqual(f.read().strip(), partition.partition_path)

  def test_no_user_site_packages(self):
    # When running instance buildout, python's user site packages are ignored
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    partition = computer.instance_list[0]
    partition.requested_state = 'started'

    # Make a broken user site package in this partition home, that will error
    # as soon as site is initialized, making python unusable. While this is
    # a bit unrealistic, real life problems were observed after installing a
    # broken buildout with `pip install --editable --user`, because user site
    # packages have priority over sys.path assignments in buildout generated
    # scripts.
    home_site_packages_dir = os.path.join(
        partition.partition_path,
        '.local',
        'lib',
        'python{version[0]}.{version[1]}'.format(version=sys.version_info),
        'site-packages',
    )
    os.makedirs(home_site_packages_dir)
    with open(os.path.join(home_site_packages_dir, 'dummy-nspkg.pth'),
              'w') as f:
      f.write('import sys; raise SystemExit("ahaha")')

    partition.software.setBuildout(textwrap.dedent('''\
      #!{sys.executable}
      print("ok")
    '''.format(sys=sys)))

    with httmock.HTTMock(computer.request_handler):
      self.assertEqual(self.grid.processComputerPartitionList(), slapgrid.SLAPGRID_SUCCESS)


class MasterMixin(BasicMixin):

  def _mock_sleep(self):
    self.fake_waiting_time = None
    self.real_sleep = time.sleep

    def mocked_sleep(secs):
      if self.fake_waiting_time is not None:
        secs = self.fake_waiting_time
      self.real_sleep(secs)

    time.sleep = mocked_sleep

  def _unmock_sleep(self):
    time.sleep = self.real_sleep

  def setUp(self):
    self._mock_sleep()
    BasicMixin.setUp(self)

  def tearDown(self):
    self._unmock_sleep()
    BasicMixin.tearDown(self)


class ComputerForTest(object):
  """
  Class to set up environment for tests setting instance, software
  and server response
  """
  def __init__(self,
               software_root,
               instance_root,
               instance_amount=1,
               software_amount=1,
               status_code=200):
    """
    Will set up instances, software and sequence
    """
    self.sequence = []
    self.instance_amount = instance_amount
    self.software_amount = software_amount
    self.software_root = software_root
    self.instance_root = instance_root
    self.status_code = status_code
    self.ip_address_list = [
            ('interface1', '10.0.8.3'),
            ('interface2', '10.0.8.4'),
            ('route_interface1', '10.10.8.4')
      ]
    if not os.path.isdir(self.instance_root):
      os.mkdir(self.instance_root)
    if not os.path.isdir(self.software_root):
      os.mkdir(self.software_root)
    self.setSoftwares()
    self.setInstances()


  def request_handler(self, url, req):
    """
    Define _callback.
    Will register global sequence of message, sequence by partition
    and error and error message by partition
    """
    self.sequence.append(url.path)
    if req.method == 'GET':
      qs = parse.parse_qs(url.query)
    else:
      qs = parse.parse_qs(req.body)
    if (url.path == '/getFullComputerInformation'
            and 'computer_id' in qs):
      slap_computer = self.getComputer(qs['computer_id'][0])
      return {
              'status_code': self.status_code,
              'content': dumps(slap_computer)
              }
    elif url.path == '/getHostingSubscriptionIpList':
      ip_address_list = self.ip_address_list
      return {
              'status_code': self.status_code,
              'content': dumps(ip_address_list)
              }
    elif url.path == '/getComputerPartitionCertificate':
      return {
              'status_code': self.status_code,
              'content': dumps({'certificate': 'SLAPOS_cert', 'key': 'SLAPOS_key'})
              }
    if req.method == 'POST' and 'computer_partition_id' in qs:
      instance = self.instance_list[int(qs['computer_partition_id'][0])]
      instance.sequence.append(url.path)
      instance.header_list.append(req.headers)
      if url.path == '/startedComputerPartition':
        instance.state = 'started'
        return {'status_code': self.status_code}
      if url.path == '/stoppedComputerPartition':
        instance.state = 'stopped'
        return {'status_code': self.status_code}
      if url.path == '/destroyedComputerPartition':
        instance.state = 'destroyed'
        return {'status_code': self.status_code}
      if url.path == '/softwareInstanceBang':
        return {'status_code': self.status_code}
      if url.path == "/updateComputerPartitionRelatedInstanceList":
        return {'status_code': self.status_code}
      if url.path == '/softwareInstanceError':
        instance.error_log = '\n'.join(
            [
                line
                for line in qs['error_log'][0].splitlines()
                if 'dropPrivileges' not in line
            ]
        )
        instance.error = True
        return {'status_code': self.status_code}

    elif req.method == 'POST' and 'url' in qs:
      # XXX hardcoded to first software release!
      software = self.software_list[0]
      software.sequence.append(url.path)
      if url.path == '/availableSoftwareRelease':
        return {'status_code': self.status_code}
      if url.path == '/buildingSoftwareRelease':
        return {'status_code': self.status_code}
      if url.path == '/destroyedSoftwareRelease':
        return {'status_code': self.status_code}
      if url.path == '/softwareReleaseError':
        software.error_log = '\n'.join(
            [
                line
                for line in qs['error_log'][0].splitlines()
                if 'dropPrivileges' not in line
            ]
        )
        software.error = True
        return {'status_code': self.status_code}

    else:
      return {'status_code': 500}

  def getTestSoftwareClass(self):
    return SoftwareForTest

  def setSoftwares(self):
    """
    Will set requested amount of software
    """
    self.software_list = [
        self.getTestSoftwareClass()(self.software_root, name=str(i))
        for i in range(self.software_amount)
    ]

  def getTestInstanceClass(self):
    return InstanceForTest

  def setInstances(self):
    """
    Will set requested amount of instance giving them by default first software
    """
    if self.software_list:
      software = self.software_list[0]
    else:
      software = None

    self.instance_list = [
        self.getTestInstanceClass()(self.instance_root, name=str(i), software=software)
        for i in range(self.instance_amount)
    ]

  def getComputer(self, computer_id):
    """
    Will return current requested state of computer
    """
    slap_computer = slapos.slap.Computer(computer_id)
    slap_computer._software_release_list = [
        software.getSoftware(computer_id)
        for software in self.software_list
    ]
    slap_computer._computer_partition_list = [
        instance.getInstance(computer_id)
        for instance in self.instance_list
    ]
    return slap_computer



class InstanceForTest(object):
  """
  Class containing all needed paramaters and function to simulate instances
  """
  def __init__(self, instance_root, name, software):
    self.instance_root = instance_root
    self.software = software
    self.requested_state = 'stopped'
    self.state = None
    self.error = False
    self.error_log = None
    self.sequence = []
    self.header_list = []
    self.name = name
    self.partition_path = os.path.join(self.instance_root, self.name)
    os.mkdir(self.partition_path, 0o750)
    self.timestamp = None
    self.ip_list = [('interface0', '10.0.8.2')]
    self.full_ip_list = [('route_interface0', '10.10.2.3', '10.10.0.1',
                          '255.0.0.0', '10.0.0.0')]

  def getInstance(self, computer_id, ):
    """
    Will return current requested state of instance
    """
    partition = slapos.slap.ComputerPartition(computer_id, self.name)
    partition._software_release_document = self.getSoftwareRelease()
    partition._requested_state = self.requested_state
    if getattr(self, 'filter_dict', None):
      partition._filter_dict = self.filter_dict
    partition._parameter_dict = {'ip_list': self.ip_list,
                                  'full_ip_list': self.full_ip_list
                                  }
    if self.software is not None:
      if self.timestamp is not None:
        partition._parameter_dict['timestamp'] = self.timestamp

    self.current_partition = partition
    return partition

  def getSoftwareRelease(self):
    """
    Return software release for Instance
    """
    if self.software is not None:
      sr = slapos.slap.SoftwareRelease()
      sr._software_release = self.software.name
      return sr
    else:
      return None

  def setPromise(self, promise_name, promise_content):
    """
    This function will set promise and return its path
    """
    promise_path = os.path.join(self.partition_path, 'etc', 'promise')
    if not os.path.isdir(promise_path):
      os.makedirs(promise_path)
    promise = os.path.join(promise_path, promise_name)
    with open(promise, 'w') as f:
      f.write(promise_content)
    os.chmod(promise, 0o777)

  def setPluginPromise(self, promise_name, success=True, failure_count=1,
      promise_content="", periodicity=0.03):
    """
    This function will set plugin promise and return its path
    """
    promise_dir = os.path.join(self.partition_path, 'etc', 'plugin')
    if not os.path.isdir(promise_dir):
      os.makedirs(promise_dir)
    _promise_content = PROMISE_CONTENT_TEMPLATE % \
         {'success': success,
          'content': promise_content,
          'failure_amount': failure_count,
          'periodicity': periodicity,
          'paths': PROMISE_PATHS}

    with open(os.path.join(promise_dir, promise_name), 'w') as f:
      f.write(_promise_content)
    return os.path.join(promise_dir, promise_name)

  def setCertificate(self, certificate_repository_path):
    if not os.path.exists(certificate_repository_path):
      os.mkdir(certificate_repository_path)
    self.cert_file = os.path.join(certificate_repository_path,
                                  "%s.crt" % self.name)
    self.certificate = str(random.random())
    with open(self.cert_file, 'w') as f:
      f.write(self.certificate)
    self.key_file = os.path.join(certificate_repository_path,
                                 '%s.key' % self.name)
    self.key = str(random.random())
    with open(self.key_file, 'w') as f:
      f.write(self.key)

class SoftwareForTest(object):
  """
  Class to prepare and simulate software.
  each instance has a software attributed
  """
  def __init__(self, software_root, name=''):
    """
    Will set file and variable for software
    """
    self.software_root = software_root
    self.name = 'http://sr%s/' % name
    self.sequence = []
    self.software_hash = md5digest(self.name)
    self.srdir = os.path.join(self.software_root, self.software_hash)
    self.requested_state = 'available'
    os.mkdir(self.srdir)
    self.setTemplateCfg()
    self.srbindir = os.path.join(self.srdir, 'bin')
    os.mkdir(self.srbindir)
    self.setBuildout()

  def getSoftware(self, computer_id):
    """
    Will return current requested state of software
    """
    software = slapos.slap.SoftwareRelease(self.name, computer_id)
    software._requested_state = self.requested_state
    return software

  def setTemplateCfg(self, template="""[buildout]"""):
    """
    Set template.cfg
    """
    with open(os.path.join(self.srdir, 'template.cfg'), 'w') as f:
      f.write(template)

  def setBuildout(self, buildout="""#!/bin/sh
touch worked"""):
    """
    Set a buildout exec in bin
    """
    with open(os.path.join(self.srbindir, 'buildout'), 'w') as f:
      f.write(buildout)
    os.chmod(os.path.join(self.srbindir, 'buildout'), 0o755)

  def setPeriodicity(self, periodicity):
    """
    Set a periodicity file
    """
    with open(os.path.join(self.srdir, 'periodicity'), 'w') as f:
      f.write(str(periodicity))


@implementer(IManager)
class DummyManager(object):
  def __init__(self):
    self.sequence = []

  def format(self, computer):
    self.sequence.append('format')

  def formatTearDown(self, computer):
    self.sequence.append('formatTearDown')

  def software(self, software):
    self.sequence.append('software')

  def softwareTearDown(self, software):
    self.sequence.append('softwareTearDown')

  def instance(self, partition):
    self.sequence.append('instance')

  def instanceTearDown(self, partition):
    self.sequence.append('instanceTearDown')

  def report(self, partition):
    self.sequence.append('report')


class TestSlapgridCPWithMaster(MasterMixin, unittest.TestCase):

  def test_nothing_to_do(self):
    computer = self.getTestComputerClass()(self.software_root, self.instance_root, 0, 0)
    with httmock.HTTMock(computer.request_handler):
      self.assertEqual(self.grid.processComputerPartitionList(), slapgrid.SLAPGRID_SUCCESS)
      self.assertInstanceDirectoryListEqual([])
      six.assertCountEqual(self, os.listdir(self.software_root), [])
      st = os.stat(os.path.join(self.instance_root, 'var'))
      self.assertEqual(stat.S_IMODE(st.st_mode), 0o755)

  def test_one_partition(self):
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    with httmock.HTTMock(computer.request_handler):
      instance = computer.instance_list[0]
      self.assertEqual(self.grid.processComputerPartitionList(), slapgrid.SLAPGRID_SUCCESS)
      self.assertInstanceDirectoryListEqual(['0'])
      partition = os.path.join(self.instance_root, '0')
      six.assertCountEqual(self, os.listdir(partition), ['.slapgrid', 'buildout.cfg',
                                                    'software_release', 'worked', '.slapos-retention-lock-delay'])
      six.assertCountEqual(self, os.listdir(self.software_root), [instance.software.software_hash])
      self.assertEqual(computer.sequence,
                       ['/getFullComputerInformation',
                        '/getComputerPartitionCertificate',
                        '/stoppedComputerPartition'])
      self.assertEqual(open(os.path.join(self.certificate_repository_path, '0.crt')).read(), 'SLAPOS_cert')
      self.assertEqual(open(os.path.join(self.certificate_repository_path, '0.key')).read(), 'SLAPOS_key')

  def test_one_partition_instance_cfg(self):
    """
    Check that slapgrid processes instance is profile is not named
    "template.cfg" but "instance.cfg".
    """
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    with httmock.HTTMock(computer.request_handler):
      instance = computer.instance_list[0]
      self.assertEqual(self.grid.processComputerPartitionList(), slapgrid.SLAPGRID_SUCCESS)
      self.assertInstanceDirectoryListEqual(['0'])
      partition = os.path.join(self.instance_root, '0')
      six.assertCountEqual(self, os.listdir(partition), ['.slapgrid', 'buildout.cfg',
                                                    'software_release', 'worked', '.slapos-retention-lock-delay'])
      six.assertCountEqual(self, os.listdir(self.software_root), [instance.software.software_hash])
      self.assertEqual(computer.sequence,
                       ['/getFullComputerInformation',
                        '/getComputerPartitionCertificate',
                        '/stoppedComputerPartition'])

  def test_one_free_partition(self):
    """
    Test if slapgrid cp does not process "free" partition
    """
    computer = self.getTestComputerClass()(self.software_root,
                               self.instance_root,
                               software_amount=0)
    with httmock.HTTMock(computer.request_handler):
      partition = computer.instance_list[0]
      partition.requested_state = 'destroyed'
      self.assertEqual(self.grid.processComputerPartitionList(), slapgrid.SLAPGRID_SUCCESS)
      self.assertInstanceDirectoryListEqual(['0'])
      six.assertCountEqual(self, os.listdir(partition.partition_path), [])
      six.assertCountEqual(self, os.listdir(self.software_root), [])
      self.assertEqual(partition.sequence, [])

  def test_one_partition_started(self):
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    with httmock.HTTMock(computer.request_handler):
      partition = computer.instance_list[0]
      partition.requested_state = 'started'
      partition.software.setBuildout(WRAPPER_CONTENT)
      self.assertEqual(self.grid.processComputerPartitionList(), slapgrid.SLAPGRID_SUCCESS)
      self.assertInstanceDirectoryListEqual(['0'])
      six.assertCountEqual(self, os.listdir(partition.partition_path),
                            ['.slapgrid', '.0_wrapper.log', 'buildout.cfg',
                             'etc', 'software_release', 'worked', '.slapos-retention-lock-delay'])
      wrapper_log = os.path.join(partition.partition_path, '.0_wrapper.log')
      self.assertLogContent(wrapper_log, 'Working')
      six.assertCountEqual(self, os.listdir(self.software_root), [partition.software.software_hash])
      self.assertEqual(computer.sequence,
                       ['/getFullComputerInformation',
                        '/getComputerPartitionCertificate',
                        '/startedComputerPartition'])
      self.assertEqual(partition.state, 'started')

  def test_one_partition_started_fail(self):
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    with httmock.HTTMock(computer.request_handler):
      partition = computer.instance_list[0]
      partition.requested_state = 'started'
      partition.software.setBuildout(WRAPPER_CONTENT)
      self.assertEqual(self.grid.processComputerPartitionList(), slapgrid.SLAPGRID_SUCCESS)
      self.assertInstanceDirectoryListEqual(['0'])
      six.assertCountEqual(self, os.listdir(partition.partition_path),
                            ['.slapgrid', '.0_wrapper.log', 'buildout.cfg',
                             'etc', 'software_release', 'worked', '.slapos-retention-lock-delay'])
      wrapper_log = os.path.join(partition.partition_path, '.0_wrapper.log')
      self.assertLogContent(wrapper_log, 'Working')
      six.assertCountEqual(self, os.listdir(self.software_root), [partition.software.software_hash])
      self.assertEqual(computer.sequence,
                       ['/getFullComputerInformation',
                        '/getComputerPartitionCertificate',
                        '/startedComputerPartition'])
      self.assertEqual(partition.state, 'started')

      instance = computer.instance_list[0]
      instance.software.setBuildout("""#!/bin/sh
exit 1
""")
      self.assertEqual(self.launchSlapgrid(), slapgrid.SLAPGRID_FAIL)
      self.assertInstanceDirectoryListEqual(['0'])
      six.assertCountEqual(self, os.listdir(instance.partition_path),
                            ['.slapgrid', '.0_wrapper.log', 'buildout.cfg',
                             'etc', 'software_release', 'worked',
                             '.slapos-retention-lock-delay', '.slapgrid-0-error.log'])
      self.assertEqual(computer.sequence,
                       ['/getFullComputerInformation',
                        '/getComputerPartitionCertificate',
                        '/startedComputerPartition',
                        '/getHateoasUrl',
                        '/getFullComputerInformation',
                        '/getComputerPartitionCertificate',
                        '/softwareInstanceError'])
      self.assertEqual(instance.state, 'started')

  def test_one_partition_started_stopped(self):
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    with httmock.HTTMock(computer.request_handler):
      instance = computer.instance_list[0]

      instance.requested_state = 'started'
      instance.software.setBuildout("""#!/bin/sh
touch worked &&
mkdir -p etc/run &&
(
cat <<'HEREDOC'
#!%(python)s
from __future__ import print_function
import signal
def handler(signum, frame):
  for i in range(30):
    print('Signal handler called with signal', signum)
  raise SystemExit
signal.signal(signal.SIGTERM, handler)

while True:
  print("Working")
HEREDOC
)> etc/run/wrapper &&
chmod 755 etc/run/wrapper
""" % {'python': sys.executable})
      self.assertEqual(self.grid.processComputerPartitionList(), slapgrid.SLAPGRID_SUCCESS)
      self.assertInstanceDirectoryListEqual(['0'])
      six.assertCountEqual(self, os.listdir(instance.partition_path),
                            ['.slapgrid', '.0_wrapper.log', 'buildout.cfg',
                             'etc', 'software_release', 'worked', '.slapos-retention-lock-delay'])
      wrapper_log = os.path.join(instance.partition_path, '.0_wrapper.log')
      self.assertLogContent(wrapper_log, 'Working')
      six.assertCountEqual(self, os.listdir(self.software_root), [instance.software.software_hash])
      self.assertEqual(computer.sequence,
                       ['/getFullComputerInformation',
                        '/getComputerPartitionCertificate',
                        '/startedComputerPartition'])
      self.assertEqual(instance.state, 'started')

      computer.sequence = []
      instance.requested_state = 'stopped'
      self.assertEqual(self.launchSlapgrid(), slapgrid.SLAPGRID_SUCCESS)
      self.assertInstanceDirectoryListEqual(['0'])
      six.assertCountEqual(self, os.listdir(instance.partition_path),
                            ['.slapgrid', '.0_wrapper.log', 'buildout.cfg',
                             'etc', 'software_release', 'worked', '.slapos-retention-lock-delay'])
      self.assertLogContent(wrapper_log, 'Signal handler called with signal 15')
      self.assertEqual(computer.sequence,
                       ['/getHateoasUrl',
                        '/getFullComputerInformation',
                        '/getComputerPartitionCertificate',
                        '/stoppedComputerPartition'])
      self.assertEqual(instance.state, 'stopped')

  def test_one_broken_partition_stopped(self):
    """
    Check that, for, an already started instance if stop is requested,
    processes will be stopped even if instance is broken (buildout fails
    to run) but status is still started.
    """
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    with httmock.HTTMock(computer.request_handler):
      instance = computer.instance_list[0]

      instance.requested_state = 'started'
      instance.software.setBuildout("""#!/bin/sh
touch worked &&
mkdir -p etc/run &&
(
cat <<'HEREDOC'
#!%(python)s
from __future__ import print_function
import signal
def handler(signum, frame):
  for i in range(30):
    print('Signal handler called with signal', signum)
  raise SystemExit
signal.signal(signal.SIGTERM, handler)

while True:
  print("Working")
HEREDOC
)> etc/run/wrapper &&
chmod 755 etc/run/wrapper
""" % {'python': sys.executable})
      self.assertEqual(self.grid.processComputerPartitionList(), slapgrid.SLAPGRID_SUCCESS)
      self.assertInstanceDirectoryListEqual(['0'])
      six.assertCountEqual(self, os.listdir(instance.partition_path),
                            ['.slapgrid', '.0_wrapper.log', 'buildout.cfg',
                             'etc', 'software_release', 'worked', '.slapos-retention-lock-delay'])
      wrapper_log = os.path.join(instance.partition_path, '.0_wrapper.log')
      self.assertLogContent(wrapper_log, 'Working')
      six.assertCountEqual(self, os.listdir(self.software_root),
                            [instance.software.software_hash])
      self.assertEqual(computer.sequence,
                       ['/getFullComputerInformation',
                        '/getComputerPartitionCertificate',
                        '/startedComputerPartition'])
      self.assertEqual(instance.state, 'started')

      computer.sequence = []
      instance.requested_state = 'stopped'
      instance.software.setBuildout("""#!/bin/sh
exit 1
""")
      self.assertEqual(self.launchSlapgrid(), slapgrid.SLAPGRID_FAIL)
      self.assertInstanceDirectoryListEqual(['0'])
      six.assertCountEqual(self, os.listdir(instance.partition_path),
                            ['.slapgrid', '.0_wrapper.log', 'buildout.cfg',
                             'etc', 'software_release', 'worked',
                             '.slapos-retention-lock-delay', '.slapgrid-0-error.log'])
      self.assertLogContent(wrapper_log, 'Signal handler called with signal 15')
      self.assertEqual(computer.sequence,
                       ['/getHateoasUrl',
                        '/getFullComputerInformation',
                        '/getComputerPartitionCertificate',
                        '/softwareInstanceError'])
      self.assertEqual(instance.state, 'started')

  def test_one_partition_stopped_started(self):
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    with httmock.HTTMock(computer.request_handler):
      instance = computer.instance_list[0]
      instance.requested_state = 'stopped'
      instance.software.setBuildout(WRAPPER_CONTENT)
      self.assertEqual(self.grid.processComputerPartitionList(), slapgrid.SLAPGRID_SUCCESS)

      self.assertInstanceDirectoryListEqual(['0'])
      partition = os.path.join(self.instance_root, '0')
      six.assertCountEqual(self, os.listdir(partition),
                            ['.slapgrid', 'buildout.cfg', 'etc', 'software_release', 'worked', '.slapos-retention-lock-delay'])
      six.assertCountEqual(self, os.listdir(self.software_root),
                            [instance.software.software_hash])
      self.assertEqual(computer.sequence,
                       ['/getFullComputerInformation',
                        '/getComputerPartitionCertificate',
                        '/stoppedComputerPartition'])
      self.assertEqual('stopped', instance.state)

      instance.requested_state = 'started'
      computer.sequence = []
      self.assertEqual(self.launchSlapgrid(), slapgrid.SLAPGRID_SUCCESS)
      self.assertInstanceDirectoryListEqual(['0'])
      partition = os.path.join(self.instance_root, '0')
      six.assertCountEqual(self, os.listdir(partition),
                            ['.slapgrid', '.0_wrapper.log', 'etc',
                             'buildout.cfg', 'software_release', 'worked', '.slapos-retention-lock-delay'])
      six.assertCountEqual(self, os.listdir(self.software_root),
                            [instance.software.software_hash])
      wrapper_log = os.path.join(instance.partition_path, '.0_wrapper.log')
      self.assertLogContent(wrapper_log, 'Working')
      self.assertEqual(computer.sequence,
                       ['/getHateoasUrl',
                        '/getFullComputerInformation',
                        '/getComputerPartitionCertificate',
                        '/startedComputerPartition'])
      self.assertEqual('started', instance.state)

  def test_one_partition_destroyed(self):
    """
    Test that an existing partition with "destroyed" status will only be
    stopped by slapgrid-cp, not processed
    """
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    with httmock.HTTMock(computer.request_handler):
      instance = computer.instance_list[0]
      instance.requested_state = 'destroyed'

      dummy_file_name = 'dummy_file'
      with open(os.path.join(instance.partition_path, dummy_file_name), 'w') as dummy_file:
        dummy_file.write('dummy')

      self.assertEqual(self.grid.processComputerPartitionList(), slapgrid.SLAPGRID_SUCCESS)

      self.assertInstanceDirectoryListEqual(['0'])
      partition = os.path.join(self.instance_root, '0')
      six.assertCountEqual(self, os.listdir(partition), ['.slapgrid', dummy_file_name])
      six.assertCountEqual(self, os.listdir(self.software_root), [instance.software.software_hash])
      self.assertEqual(computer.sequence,
                       ['/getFullComputerInformation',
                        '/getComputerPartitionCertificate',
                        '/stoppedComputerPartition'])
      self.assertEqual('stopped', instance.state)

  def test_one_partition_started_no_master(self):
    computer = self.getTestComputerClass()(self.software_root, self.instance_root, status_code=503)
    with httmock.HTTMock(computer.request_handler):
      partition = computer.instance_list[0]
      partition.requested_state = 'started'
      partition.software.setBuildout()
      self.assertEqual(self.grid.processComputerPartitionList(), slapgrid.SLAPGRID_OFFLINE_SUCCESS)
      self.assertInstanceDirectoryListEqual(['0'])
      six.assertCountEqual(self, os.listdir(partition.partition_path), []) # buildout hasn't run
      six.assertCountEqual(self, os.listdir(self.software_root), [partition.software.software_hash])
      self.assertEqual(computer.sequence, ['/getFullComputerInformation'])
      self.assertEqual(partition.state, None)

  def test_one_partition_started_after_master_connection_loss(self):
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    partition = computer.instance_list[0]
    partition.requested_state = 'started'
    partition.software.setBuildout()
    run_path = os.path.join(partition.partition_path, 'etc', 'run')
    os.makedirs(run_path)
    with open(os.path.join(run_path, 'runner'), 'w') as f:
      f.write("#!/bin/sh\necho 'Working'\ntouch 'runner_worked'")
      os.fchmod(f.fileno(), 0o755)

    runner_worked_file = os.path.join(partition.partition_path, 'runner_worked')
    def assertRunnerWorked():
      for _ in range(50):
        if os.path.exists(runner_worked_file):
          break
        time.sleep(0.1)
      else:
        self.assertTrue(os.path.exists(runner_worked_file))

    with httmock.HTTMock(computer.request_handler):
      self.assertEqual(self.grid.processComputerPartitionList(), slapgrid.SLAPGRID_SUCCESS)
      self.assertInstanceDirectoryListEqual(['0'])
      assertRunnerWorked()
      six.assertCountEqual(self, os.listdir(partition.partition_path),
                            ['.slapgrid', '.0_runner.log', 'buildout.cfg', 'etc',
                             'runner_worked', 'software_release', 'worked',
                             '.slapos-retention-lock-delay'])
      runner_log_path = os.path.join(partition.partition_path, '.0_runner.log')
      with open(runner_log_path) as f:
        runner_log = f.read()
      self.assertEqual(runner_log, 'Working\n')
      self.assertEqual(partition.state, 'started')

    computer.status_code = 503 # connection loss
    os.unlink(runner_worked_file)

    with httmock.HTTMock(computer.request_handler):
      self.assertEqual(self.grid.processComputerPartitionList(), slapgrid.SLAPGRID_OFFLINE_SUCCESS)
      self.assertInstanceDirectoryListEqual(['0'])
      assertRunnerWorked()
      with open(runner_log_path) as f:
        runner_log = f.read()
      self.assertEqual(runner_log, 'Working\n' * 2)
      self.assertEqual(computer.sequence, [
        '/getFullComputerInformation',
        '/getComputerPartitionCertificate',
        '/startedComputerPartition',
        '/getComputerPartitionCertificate' # /getFullComputerInformation is cached
      ])

  def test_stopped_partition_remains_stopped_after_master_connection_loss(self):
    computer = self.getTestComputerClass()(
      self.software_root, self.instance_root, instance_amount=2)

    for i in range(2):
      partition = computer.instance_list[i]
      partition.requested_state = 'started'
      partition.software.setBuildout()
      run_path = os.path.join(partition.partition_path, 'etc', 'run')
      os.makedirs(run_path)
      with open(os.path.join(run_path, 'runner'), 'w') as f:
        f.write("#!/bin/sh\necho 'Working'\ntouch 'runner_worked'")
        os.fchmod(f.fileno(), 0o755)

    control_partition = computer.instance_list[0]
    test_partition = computer.instance_list[1]

    control_file = os.path.join(control_partition.partition_path, 'runner_worked')
    test_file = os.path.join(test_partition.partition_path, 'runner_worked')

    def assertRunnerWorked(path):
      for _ in range(50):
        if os.path.exists(path):
          break
        time.sleep(0.1)
      else:
        self.assertTrue(os.path.exists(path))

    with httmock.HTTMock(computer.request_handler):
      self.assertEqual(self.grid.processComputerPartitionList(), slapgrid.SLAPGRID_SUCCESS)
      self.assertInstanceDirectoryListEqual(['0', '1'])
      assertRunnerWorked(control_file)
      assertRunnerWorked(test_file)
      for i in range(2):
        six.assertCountEqual(self, os.listdir(computer.instance_list[i].partition_path),
                              ['.slapgrid', '.%d_runner.log' % i, 'buildout.cfg', 'etc',
                              'runner_worked', 'software_release', 'worked',
                              '.slapos-retention-lock-delay'])
      self.assertEqual(control_partition.state, 'started')
      self.assertEqual(test_partition.state, 'started')

    # simulate stopping the partition with old version
    test_partition.state = 'stopped'
    state_path = os.path.join(test_partition.partition_path, '.requested_state')
    with open(state_path, 'w') as f:
      f.write('stopped')

    computer.status_code = 503 # connection loss
    os.unlink(control_file)
    os.unlink(test_file)

    with httmock.HTTMock(computer.request_handler):
      self.assertEqual(self.grid.processComputerPartitionList(), slapgrid.SLAPGRID_OFFLINE_SUCCESS)
      self.assertInstanceDirectoryListEqual(['0', '1'])
      assertRunnerWorked(control_file)
      self.assertFalse(os.path.exists(test_file))
      self.assertEqual(computer.sequence, [
        '/getFullComputerInformation',
        '/getComputerPartitionCertificate',
        '/startedComputerPartition',
        '/getComputerPartitionCertificate',
        '/startedComputerPartition',
        '/getComputerPartitionCertificate' # /getFullComputerInformation is cached
      ])

class TestSlapgridCPWithMasterWatchdog(MasterMixin, unittest.TestCase):

  def setUp(self):
    MasterMixin.setUp(self)
    # Prepare watchdog
    self.watchdog_banged = os.path.join(self._tempdir, 'watchdog_banged')
    watchdog_path = os.path.join(self._tempdir, 'watchdog')
    with open(watchdog_path, 'w') as f:
      f.write(WATCHDOG_TEMPLATE.format(
          python_path=sys.executable,
          sys_path=sys.path,
          watchdog_banged=self.watchdog_banged
      ))
    os.chmod(watchdog_path, 0o755)
    self.grid.watchdog_path = watchdog_path
    slapos.grid.slapgrid.WATCHDOG_PATH = watchdog_path

  def test_one_failing_daemon_in_service_will_bang_with_watchdog(self):
    """
    Check that a failing service watched by watchdog trigger bang
    1.Prepare computer and set a service named daemon in etc/service
       (to be watched by watchdog). This daemon will fail.
    2.Prepare file for supervisord to call watchdog
       -Set sys.path
       -Monkeypatch computer partition bang
    3.Check damemon is launched
    4.Wait for it to fail
    5.Wait for file generated by monkeypacthed bang to appear
    """
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    with httmock.HTTMock(computer.request_handler):
      partition = computer.instance_list[0]
      partition.requested_state = 'started'
      partition.software.setBuildout(DAEMON_CONTENT)

      self.assertEqual(self.grid.processComputerPartitionList(), slapgrid.SLAPGRID_SUCCESS)
      self.assertInstanceDirectoryListEqual(['0'])
      six.assertCountEqual(self, os.listdir(partition.partition_path),
                            ['.slapgrid', '.0_daemon.log', 'buildout.cfg',
                             'etc', 'software_release', 'worked', '.slapos-retention-lock-delay'])
      daemon_log = os.path.join(partition.partition_path, '.0_daemon.log')
      self.assertLogContent(daemon_log, 'Failing')
      self.assertIsCreated(self.watchdog_banged)
      with open(self.watchdog_banged) as f:
        self.assertIn('daemon', f.read())

  def test_one_failing_daemon_in_run_will_not_bang_with_watchdog(self):
    """
    Check that a failing service watched by watchdog does not trigger bang
    1.Prepare computer and set a service named daemon in etc/run
       (not watched by watchdog). This daemon will fail.
    2.Prepare file for supervisord to call watchdog
       -Set sys.path
       -Monkeypatch computer partition bang
    3.Check damemon is launched
    4.Wait for it to fail
    5.Check that file generated by monkeypacthed bang do not appear
    """
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    with httmock.HTTMock(computer.request_handler):
      partition = computer.instance_list[0]
      partition.requested_state = 'started'

      # Content of run wrapper
      WRAPPER_CONTENT = textwrap.dedent("""#!/bin/sh
          touch ./launched
          touch ./crashed
          echo Failing
          sleep 1
          exit 111
      """)

      BUILDOUT_RUN_CONTENT = textwrap.dedent("""#!/bin/sh
          mkdir -p etc/run &&
          echo "%s" >> etc/run/daemon &&
          chmod 755 etc/run/daemon &&
          touch worked
          """ % WRAPPER_CONTENT)

      partition.software.setBuildout(BUILDOUT_RUN_CONTENT)

      self.assertEqual(self.grid.processComputerPartitionList(), slapgrid.SLAPGRID_SUCCESS)
      time.sleep(1)
      self.assertInstanceDirectoryListEqual(['0'])
      six.assertCountEqual(self, os.listdir(partition.partition_path),
                            ['.slapgrid', '.0_daemon.log', 'buildout.cfg',
                             'etc', 'software_release', 'worked', '.slapos-retention-lock-delay',
                             'launched', 'crashed'])
      daemon_log = os.path.join(partition.partition_path, '.0_daemon.log')
      self.assertLogContent(daemon_log, 'Failing')
      self.assertIsNotCreated(self.watchdog_banged)

  def test_watched_by_watchdog_bang(self):
    """
    Test that a process going to fatal or exited mode in supervisord
    is banged if watched by watchdog
    Certificates used for the bang are also checked
    (ie: watchdog id in process name)
    """
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    with httmock.HTTMock(computer.request_handler):
      instance = computer.instance_list[0]
      certificate_repository_path = os.path.join(self._tempdir, 'partition_pki')
      instance.setCertificate(certificate_repository_path)

      watchdog = Watchdog(
          master_url='https://127.0.0.1/',
          computer_id=self.computer_id,
          certificate_repository_path=certificate_repository_path
      )
      for event in watchdog.process_state_events:
        instance.sequence = []
        instance.header_list = []
        headers = {'eventname': event}
        payload = 'processname:%s groupname:%s from_state:RUNNING' % (
            'daemon' + WATCHDOG_MARK, instance.name)
        watchdog.handle_event(headers, payload)
        self.assertEqual(instance.sequence, ['/softwareInstanceBang'])

  def test_unwanted_events_will_not_bang(self):
    """
    Test that a process going to a mode not watched by watchdog
    in supervisord is not banged if watched by watchdog
    """
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    instance = computer.instance_list[0]

    watchdog = Watchdog(
        master_url=self.master_url,
        computer_id=self.computer_id,
        certificate_repository_path=None
    )
    for event in ['EVENT', 'PROCESS_STATE', 'PROCESS_STATE_RUNNING',
                  'PROCESS_STATE_BACKOFF', 'PROCESS_STATE_STOPPED']:
      computer.sequence = []
      headers = {'eventname': event}
      payload = 'processname:%s groupname:%s from_state:RUNNING' % (
          'daemon' + WATCHDOG_MARK, instance.name)
      watchdog.handle_event(headers, payload)
      self.assertEqual(instance.sequence, [])

  def test_not_watched_by_watchdog_do_not_bang(self):
    """
    Test that a process going to fatal or exited mode in supervisord
    is not banged if not watched by watchdog
    (ie: no watchdog id in process name)
    """
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    instance = computer.instance_list[0]

    watchdog = Watchdog(
        master_url=self.master_url,
        computer_id=self.computer_id,
        certificate_repository_path=None
    )
    for event in watchdog.process_state_events:
      computer.sequence = []
      headers = {'eventname': event}
      payload = "processname:%s groupname:%s from_state:RUNNING"\
          % ('daemon', instance.name)
      watchdog.handle_event(headers, payload)
      self.assertEqual(computer.sequence, [])

  def test_watchdog_create_bang_file_after_bang(self):
    """
    For a partition that has been successfully deployed (thus .timestamp file
    existing), check that bang file is created and contains the timestamp of
    .timestamp file.
    """
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    with httmock.HTTMock(computer.request_handler):
      instance = computer.instance_list[0]
      certificate_repository_path = os.path.join(self._tempdir, 'partition_pki')
      instance.setCertificate(certificate_repository_path)
      partition = os.path.join(self.instance_root, '0')
      timestamp_content = '1234'
      timestamp_file = open(os.path.join(partition, slapos.grid.slapgrid.COMPUTER_PARTITION_TIMESTAMP_FILENAME), 'w')
      timestamp_file.write(timestamp_content)
      timestamp_file.close()

      watchdog = Watchdog(
          master_url='https://127.0.0.1/',
          computer_id=self.computer_id,
          certificate_repository_path=certificate_repository_path,
          instance_root_path=self.instance_root
      )
      event = watchdog.process_state_events[0]
      instance.sequence = []
      instance.header_list = []
      headers = {'eventname': event}
      payload = 'processname:%s groupname:%s from_state:RUNNING' % (
          'daemon' + WATCHDOG_MARK, instance.name)
      watchdog.handle_event(headers, payload)
      self.assertEqual(instance.sequence, ['/softwareInstanceBang'])

      with open(os.path.join(
          partition,
          slapos.grid.slapgrid.COMPUTER_PARTITION_LATEST_BANG_TIMESTAMP_FILENAME)) as f:
        self.assertEqual(f.read(), timestamp_content)

  def test_watchdog_ignore_bang_if_partition_not_deployed(self):
    """
    For a partition that has never been successfully deployed (buildout is
    failing, promise is not passing, etc), test that bang is ignored.

    Practically speaking, .timestamp file in the partition does not exsit.
    """
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    with httmock.HTTMock(computer.request_handler):
      instance = computer.instance_list[0]
      certificate_repository_path = os.path.join(self._tempdir, 'partition_pki')
      instance.setCertificate(certificate_repository_path)
      partition = os.path.join(self.instance_root, '0')
      timestamp_content = '1234'

      watchdog = Watchdog(
          master_url='https://127.0.0.1/',
          computer_id=self.computer_id,
          certificate_repository_path=certificate_repository_path,
          instance_root_path=self.instance_root
      )
      event = watchdog.process_state_events[0]
      instance.sequence = []
      instance.header_list = []
      headers = {'eventname': event}
      payload = 'processname:%s groupname:%s from_state:RUNNING' % (
          'daemon' + WATCHDOG_MARK, instance.name)
      watchdog.handle_event(headers, payload)
      self.assertEqual(instance.sequence, ['/softwareInstanceBang'])

      with open(os.path.join(
          partition,
          slapos.grid.slapgrid.COMPUTER_PARTITION_LATEST_BANG_TIMESTAMP_FILENAME)) as f:
        self.assertNotEqual(f.read(), timestamp_content)

  def test_watchdog_bang_only_once_if_partition_never_deployed(self):
    """
    For a partition that has been never successfully deployed (promises are not passing,
    etc), test that:
     * First bang is transmitted
     * subsequent bangs are ignored until a deployment is successful.
    """
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    with httmock.HTTMock(computer.request_handler):
      instance = computer.instance_list[0]
      certificate_repository_path = os.path.join(self._tempdir, 'partition_pki')
      instance.setCertificate(certificate_repository_path)
      partition = os.path.join(self.instance_root, '0')

      watchdog = Watchdog(
          master_url='https://127.0.0.1/',
          computer_id=self.computer_id,
          certificate_repository_path=certificate_repository_path,
          instance_root_path=self.instance_root
      )
      # First bang
      event = watchdog.process_state_events[0]
      instance.sequence = []
      instance.header_list = []
      headers = {'eventname': event}
      payload = 'processname:%s groupname:%s from_state:RUNNING' % (
          'daemon' + WATCHDOG_MARK, instance.name)
      watchdog.handle_event(headers, payload)
      self.assertEqual(instance.sequence, ['/softwareInstanceBang'])

      # Second bang
      event = watchdog.process_state_events[0]
      instance.sequence = []
      instance.header_list = []
      headers = {'eventname': event}
      payload = 'processname:%s groupname:%s from_state:RUNNING' % (
          'daemon' + WATCHDOG_MARK, instance.name)
      watchdog.handle_event(headers, payload)
      self.assertEqual(instance.sequence, [])


  def test_watchdog_bang_only_once_if_timestamp_did_not_change(self):
    """
    For a partition that has been successfully deployed (promises are passing,
    etc), test that:
     * First bang is transmitted
     * subsequent bangs are ignored until a new deployment is successful.
    Scenario:
     * slapgrid successfully deploys a partition
     * A process crashes, watchdog calls bang
     * Another deployment (run of slapgrid) is done, but not successful (
       promise is failing)
     * The process crashes again, but watchdog ignores it
     * Yet another deployment is done, and it is successful
     * The process crashes again, watchdog calls bang
     * The process crashes again, watchdog ignroes it
    """
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    with httmock.HTTMock(computer.request_handler):
      instance = computer.instance_list[0]
      certificate_repository_path = os.path.join(self._tempdir, 'partition_pki')
      instance.setCertificate(certificate_repository_path)
      partition = os.path.join(self.instance_root, '0')
      timestamp_content = '1234'
      timestamp_file = open(os.path.join(partition, slapos.grid.slapgrid.COMPUTER_PARTITION_TIMESTAMP_FILENAME), 'w')
      timestamp_file.write(timestamp_content)
      timestamp_file.close()

      watchdog = Watchdog(
          master_url='https://127.0.0.1/',
          computer_id=self.computer_id,
          certificate_repository_path=certificate_repository_path,
          instance_root_path=self.instance_root
      )
      # First bang
      event = watchdog.process_state_events[0]
      instance.sequence = []
      instance.header_list = []
      headers = {'eventname': event}
      payload = 'processname:%s groupname:%s from_state:RUNNING' % (
          'daemon' + WATCHDOG_MARK, instance.name)
      watchdog.handle_event(headers, payload)
      self.assertEqual(instance.sequence, ['/softwareInstanceBang'])

      with open(os.path.join(
          partition,
          slapos.grid.slapgrid.COMPUTER_PARTITION_LATEST_BANG_TIMESTAMP_FILENAME)) as f:
        self.assertEqual(f.read(), timestamp_content)

      # Second bang
      event = watchdog.process_state_events[0]
      instance.sequence = []
      instance.header_list = []
      headers = {'eventname': event}
      payload = 'processname:%s groupname:%s from_state:RUNNING' % (
          'daemon' + WATCHDOG_MARK, instance.name)
      watchdog.handle_event(headers, payload)
      self.assertEqual(instance.sequence, [])

      # Second successful deployment
      timestamp_content = '12345'
      timestamp_file = open(os.path.join(partition, slapos.grid.slapgrid.COMPUTER_PARTITION_TIMESTAMP_FILENAME), 'w')
      timestamp_file.write(timestamp_content)
      timestamp_file.close()

      # Third bang
      event = watchdog.process_state_events[0]
      instance.sequence = []
      instance.header_list = []
      headers = {'eventname': event}
      payload = 'processname:%s groupname:%s from_state:RUNNING' % (
          'daemon' + WATCHDOG_MARK, instance.name)
      watchdog.handle_event(headers, payload)
      self.assertEqual(instance.sequence, ['/softwareInstanceBang'])

      with open(os.path.join(
          partition,
          slapos.grid.slapgrid.COMPUTER_PARTITION_LATEST_BANG_TIMESTAMP_FILENAME)) as f:
        self.assertEqual(f.read(), timestamp_content)

      # Fourth bang
      event = watchdog.process_state_events[0]
      instance.sequence = []
      instance.header_list = []
      headers = {'eventname': event}
      payload = 'processname:%s groupname:%s from_state:RUNNING' % (
          'daemon' + WATCHDOG_MARK, instance.name)
      watchdog.handle_event(headers, payload)
      self.assertEqual(instance.sequence, [])


class TestSlapgridCPPartitionProcessing(MasterMixin, unittest.TestCase):

  def test_partition_timestamp(self):
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    with httmock.HTTMock(computer.request_handler):
      instance = computer.instance_list[0]
      timestamp = str(int(time.time()))
      instance.timestamp = timestamp

      self.assertEqual(self.grid.processComputerPartitionList(), slapgrid.SLAPGRID_SUCCESS)
      self.assertInstanceDirectoryListEqual(['0'])
      partition = os.path.join(self.instance_root, '0')
      six.assertCountEqual(self, os.listdir(partition),
                            ['.slapgrid', '.timestamp', 'buildout.cfg', 'software_release', 'worked', '.slapos-retention-lock-delay'])
      six.assertCountEqual(self, os.listdir(self.software_root), [instance.software.software_hash])
      timestamp_path = os.path.join(instance.partition_path, '.timestamp')
      self.setSlapgrid()
      self.assertEqual(self.grid.processComputerPartitionList(), slapgrid.SLAPGRID_SUCCESS)
      with open(timestamp_path) as f:
        self.assertIn(timestamp, f.read())
      self.assertEqual(instance.sequence,
                       ['/stoppedComputerPartition'])

  def test_partition_timestamp_develop(self):
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    with httmock.HTTMock(computer.request_handler):
      instance = computer.instance_list[0]
      timestamp = str(int(time.time()))
      instance.timestamp = timestamp

      self.assertEqual(self.grid.processComputerPartitionList(), slapgrid.SLAPGRID_SUCCESS)
      self.assertInstanceDirectoryListEqual(['0'])
      partition = os.path.join(self.instance_root, '0')
      six.assertCountEqual(self, os.listdir(partition),
                            ['.slapgrid', '.timestamp', 'buildout.cfg',
                             'software_release', 'worked', '.slapos-retention-lock-delay'])
      six.assertCountEqual(self, os.listdir(self.software_root), [instance.software.software_hash])

      self.assertEqual(self.launchSlapgrid(develop=True),
                       slapgrid.SLAPGRID_SUCCESS)
      self.assertEqual(self.launchSlapgrid(), slapgrid.SLAPGRID_SUCCESS)

      self.assertEqual(instance.sequence,
                       [ '/stoppedComputerPartition',
                         '/stoppedComputerPartition'])

  def test_partition_old_timestamp(self):
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    with httmock.HTTMock(computer.request_handler):
      instance = computer.instance_list[0]
      timestamp = str(int(time.time()))
      instance.timestamp = timestamp

      self.assertEqual(self.grid.processComputerPartitionList(), slapgrid.SLAPGRID_SUCCESS)
      self.assertInstanceDirectoryListEqual(['0'])
      partition = os.path.join(self.instance_root, '0')
      six.assertCountEqual(self, os.listdir(partition),
                            ['.slapgrid', '.timestamp', 'buildout.cfg', 'software_release', 'worked', '.slapos-retention-lock-delay'])
      six.assertCountEqual(self, os.listdir(self.software_root), [instance.software.software_hash])
      instance.timestamp = str(int(timestamp) - 1)
      self.assertEqual(self.launchSlapgrid(), slapgrid.SLAPGRID_SUCCESS)
      self.assertEqual(instance.sequence,
                       [ '/stoppedComputerPartition'])

  def test_partition_timestamp_new_timestamp(self):
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    with httmock.HTTMock(computer.request_handler):
      instance = computer.instance_list[0]
      timestamp = str(int(time.time()))
      instance.timestamp = timestamp

      self.assertEqual(self.launchSlapgrid(), slapgrid.SLAPGRID_SUCCESS)
      self.assertInstanceDirectoryListEqual(['0'])
      partition = os.path.join(self.instance_root, '0')
      six.assertCountEqual(self, os.listdir(partition),
                            ['.slapgrid', '.timestamp', 'buildout.cfg', 'software_release', 'worked', '.slapos-retention-lock-delay'])
      six.assertCountEqual(self, os.listdir(self.software_root), [instance.software.software_hash])
      instance.timestamp = str(int(timestamp) + 1)
      self.assertEqual(self.launchSlapgrid(), slapgrid.SLAPGRID_SUCCESS)
      self.assertEqual(self.launchSlapgrid(), slapgrid.SLAPGRID_SUCCESS)
      self.assertEqual(computer.sequence,
                       ['/getHateoasUrl',
                        '/getFullComputerInformation',
                        '/getComputerPartitionCertificate',
                        '/stoppedComputerPartition',
                        '/getHateoasUrl',
                        '/getFullComputerInformation',
                        '/getComputerPartitionCertificate',
                        '/stoppedComputerPartition',
                        '/getHateoasUrl',
                        '/getFullComputerInformation'])

  def test_partition_timestamp_no_timestamp(self):
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    with httmock.HTTMock(computer.request_handler):
      instance = computer.instance_list[0]
      timestamp = str(int(time.time()))
      instance.timestamp = timestamp

      self.launchSlapgrid()
      self.assertInstanceDirectoryListEqual(['0'])
      partition = os.path.join(self.instance_root, '0')
      six.assertCountEqual(self, os.listdir(partition),
                            ['.slapgrid', '.timestamp', 'buildout.cfg', 'software_release', 'worked', '.slapos-retention-lock-delay'])
      six.assertCountEqual(self, os.listdir(self.software_root),
                            [instance.software.software_hash])
      instance.timestamp = None
      self.launchSlapgrid()
      self.assertEqual(computer.sequence,
                       ['/getHateoasUrl',
                        '/getFullComputerInformation',
                        '/getComputerPartitionCertificate',
                        '/stoppedComputerPartition',
                        '/getHateoasUrl',
                        '/getFullComputerInformation',
                        '/getComputerPartitionCertificate',
                        '/stoppedComputerPartition'])

  def test_partition_periodicity_remove_timestamp(self):
    """
    Check that if periodicity forces run of buildout for a partition, it
    removes the .timestamp file.
    """
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    with httmock.HTTMock(computer.request_handler):
      instance = computer.instance_list[0]
      timestamp = str(int(time.time()))

      instance.timestamp = timestamp
      instance.requested_state = 'started'
      instance.software.setPeriodicity(1)

      self.launchSlapgrid()
      partition = os.path.join(self.instance_root, '0')
      six.assertCountEqual(self, os.listdir(partition),
                            ['.slapgrid', '.timestamp', 'buildout.cfg',
                             'software_release', 'worked', '.slapos-retention-lock-delay'])

      time.sleep(2)
      # dummify install() so that it doesn't actually do anything so that it
      # doesn't recreate .timestamp.
      instance.install = lambda: None

      self.launchSlapgrid()
      six.assertCountEqual(self, os.listdir(partition),
                            ['.slapgrid', '.timestamp', 'buildout.cfg',
                             'software_release', 'worked', '.slapos-retention-lock-delay'])

  def test_one_partition_periodicity_from_file_does_not_disturb_others(self):
    """
    If time between last processing of instance and now is superior
    to periodicity then instance should be proceed
    1. We set a wanted maximum_periodicity in periodicity file in
        in one software release directory and not the other one
    2. We process computer partition and check if wanted_periodicity was
        used as maximum_periodicty
    3. We wait for a time superior to wanted_periodicty
    4. We launch processComputerPartition and check that partition using
        software with periodicity was runned and not the other
    5. We check that modification time of .timestamp was modified
    """
    computer = self.getTestComputerClass()(self.software_root, self.instance_root, 20, 20)
    with httmock.HTTMock(computer.request_handler):
      instance0 = computer.instance_list[0]
      timestamp = str(int(time.time() - 5))
      instance0.timestamp = timestamp
      instance0.requested_state = 'started'
      for instance in computer.instance_list[1:]:
        instance.software = \
            computer.software_list[computer.instance_list.index(instance)]
        instance.timestamp = timestamp

      wanted_periodicity = 1
      instance0.software.setPeriodicity(wanted_periodicity)

      self.launchSlapgrid()
      self.assertNotEqual(wanted_periodicity, self.grid.maximum_periodicity)
      last_runtime = os.path.getmtime(
          os.path.join(instance0.partition_path, '.timestamp'))
      time.sleep(wanted_periodicity + 1)
      for instance in computer.instance_list[1:]:
        self.assertEqual(instance.sequence,
                         [ '/stoppedComputerPartition'])
      time.sleep(1)
      self.launchSlapgrid()
      self.assertEqual(instance0.sequence,
                       [ '/startedComputerPartition',
                         '/startedComputerPartition',
                        ])
      for instance in computer.instance_list[1:]:
        self.assertEqual(instance.sequence,
                         [ '/stoppedComputerPartition'])
      self.assertGreater(
          os.path.getmtime(os.path.join(instance0.partition_path, '.timestamp')),
          last_runtime)
      self.assertNotEqual(wanted_periodicity, self.grid.maximum_periodicity)

  def test_one_partition_stopped_is_not_processed_after_periodicity(self):
    """
    Check that periodicity forces processing a partition even if it is not
    started.
    """
    computer = self.getTestComputerClass()(self.software_root, self.instance_root, 20, 20)
    with httmock.HTTMock(computer.request_handler):
      instance0 = computer.instance_list[0]
      timestamp = str(int(time.time() - 5))
      instance0.timestamp = timestamp
      for instance in computer.instance_list[1:]:
        instance.software = \
            computer.software_list[computer.instance_list.index(instance)]
        instance.timestamp = timestamp

      wanted_periodicity = 1
      instance0.software.setPeriodicity(wanted_periodicity)

      self.launchSlapgrid()
      self.assertNotEqual(wanted_periodicity, self.grid.maximum_periodicity)
      last_runtime = os.path.getmtime(
          os.path.join(instance0.partition_path, '.timestamp'))
      time.sleep(wanted_periodicity + 1)
      for instance in computer.instance_list[1:]:
        self.assertEqual(instance.sequence,
                         [ '/stoppedComputerPartition'])
      time.sleep(1)
      self.launchSlapgrid()
      self.assertEqual(instance0.sequence,
                       [ '/stoppedComputerPartition',
                         '/stoppedComputerPartition'])
      for instance in computer.instance_list[1:]:
        self.assertEqual(instance.sequence,
                         [ '/stoppedComputerPartition'])
      self.assertNotEqual(os.path.getmtime(os.path.join(instance0.partition_path,
                                                        '.timestamp')),
                          last_runtime)
      self.assertNotEqual(wanted_periodicity, self.grid.maximum_periodicity)

  def test_one_partition_destroyed_is_not_processed_after_periodicity(self):
    """
    Check that periodicity forces processing a partition even if it is not
    started.
    """
    computer = self.getTestComputerClass()(self.software_root, self.instance_root, 20, 20)
    with httmock.HTTMock(computer.request_handler):
      instance0 = computer.instance_list[0]
      timestamp = str(int(time.time() - 5))
      instance0.timestamp = timestamp
      instance0.requested_state = 'stopped'
      for instance in computer.instance_list[1:]:
        instance.software = \
            computer.software_list[computer.instance_list.index(instance)]
        instance.timestamp = timestamp

      wanted_periodicity = 1
      instance0.software.setPeriodicity(wanted_periodicity)

      self.launchSlapgrid()
      self.assertNotEqual(wanted_periodicity, self.grid.maximum_periodicity)
      last_runtime = os.path.getmtime(
          os.path.join(instance0.partition_path, '.timestamp'))
      time.sleep(wanted_periodicity + 1)
      for instance in computer.instance_list[1:]:
        self.assertEqual(instance.sequence,
                         [ '/stoppedComputerPartition'])
      time.sleep(1)
      instance0.requested_state = 'destroyed'
      self.launchSlapgrid()
      self.assertEqual(instance0.sequence,
                       [ '/stoppedComputerPartition',
                                                       '/stoppedComputerPartition'])
      for instance in computer.instance_list[1:]:
        self.assertEqual(instance.sequence,
                         [ '/stoppedComputerPartition'])
      self.assertNotEqual(os.path.getmtime(os.path.join(instance0.partition_path,
                                                        '.timestamp')),
                          last_runtime)
      self.assertNotEqual(wanted_periodicity, self.grid.maximum_periodicity)

  def test_one_partition_is_never_processed_when_periodicity_is_negative(self):
    """
    Checks that a partition is not processed when
    its periodicity is negative
    1. We setup one instance and set periodicity at -1
    2. We mock the install method from slapos.grid.slapgrid.Partition
    3. We launch slapgrid once so that .timestamp file is created and check that install method is
    indeed called (through mocked_method.called
    4. We launch slapgrid anew and check that install as not been called again
    """

    computer = self.getTestComputerClass()(self.software_root, self.instance_root, 1, 1)
    with httmock.HTTMock(computer.request_handler):
      timestamp = str(int(time.time()))
      instance = computer.instance_list[0]
      instance.software.setPeriodicity(-1)
      instance.timestamp = timestamp
      with patch.object(slapos.grid.slapgrid.Partition, 'install', return_value=None) as mock_method:
        self.launchSlapgrid()
        self.assertTrue(mock_method.called)
        self.launchSlapgrid()
        self.assertEqual(mock_method.call_count, 1)

  def test_one_partition_is_always_processed_when_periodicity_is_zero(self):
    """
    Checks that a partition is always processed when
    its periodicity is 0
    1. We setup one instance and set periodicity at 0
    2. We mock the install method from slapos.grid.slapgrid.Partition
    3. We launch slapgrid once so that .timestamp file is created
    4. We launch slapgrid anew and check that install has been called twice (one time because of the
    new setup and one time because of periodicity = 0)
    """

    computer = self.getTestComputerClass()(self.software_root, self.instance_root, 1, 1)
    with httmock.HTTMock(computer.request_handler):
      timestamp = str(int(time.time()))
      instance = computer.instance_list[0]
      instance.software.setPeriodicity(0)
      instance.timestamp = timestamp
      with patch.object(slapos.grid.slapgrid.Partition, 'install', return_value=None) as mock_method:
        self.launchSlapgrid()
        self.launchSlapgrid()
        self.assertEqual(mock_method.call_count, 2)

  def test_one_partition_buildout_fail_does_not_disturb_others(self):
    """
    1. We set up two instance one using a corrupted buildout
    2. One will fail but the other one will be processed correctly
    """
    computer = self.getTestComputerClass()(self.software_root, self.instance_root, 2, 2)
    with httmock.HTTMock(computer.request_handler):
      instance0 = computer.instance_list[0]
      instance1 = computer.instance_list[1]
      instance1.software = computer.software_list[1]
      instance0.software.setBuildout("""#!/bin/sh
exit 42""")
      self.launchSlapgrid()
      self.assertEqual(instance0.sequence,
                       ['/softwareInstanceError'])
      self.assertEqual(instance1.sequence,
                       [ '/stoppedComputerPartition'])

  def test_one_partition_lacking_software_path_does_not_disturb_others(self):
    """
    1. We set up two instance but remove software path of one
    2. One will fail but the other one will be processed correctly
    """
    computer = self.getTestComputerClass()(self.software_root, self.instance_root, 2, 2)
    with httmock.HTTMock(computer.request_handler):
      instance0 = computer.instance_list[0]
      instance1 = computer.instance_list[1]
      instance1.software = computer.software_list[1]
      shutil.rmtree(instance0.software.srdir)
      self.launchSlapgrid()
      self.assertEqual(instance0.sequence,
                       ['/softwareInstanceError'])
      self.assertEqual(instance1.sequence,
                       [ '/stoppedComputerPartition'])

  def test_one_partition_lacking_software_bin_path_does_not_disturb_others(self):
    """
    1. We set up two instance but remove software bin path of one
    2. One will fail but the other one will be processed correctly
    """
    computer = self.getTestComputerClass()(self.software_root, self.instance_root, 2, 2)
    with httmock.HTTMock(computer.request_handler):
      instance0 = computer.instance_list[0]
      instance1 = computer.instance_list[1]
      instance1.software = computer.software_list[1]
      shutil.rmtree(instance0.software.srbindir)
      self.launchSlapgrid()
      self.assertEqual(instance0.sequence,
                       ['/softwareInstanceError'])
      self.assertEqual(instance1.sequence,
                       [ '/stoppedComputerPartition'])

  def test_one_partition_lacking_path_does_not_disturb_others(self):
    """
    1. We set up two instances but remove path of one
    2. One will fail but the other one will be processed correctly
    """
    computer = self.getTestComputerClass()(self.software_root, self.instance_root, 2, 2)
    with httmock.HTTMock(computer.request_handler):
      instance0 = computer.instance_list[0]
      instance1 = computer.instance_list[1]
      instance1.software = computer.software_list[1]
      shutil.rmtree(instance0.partition_path)
      self.launchSlapgrid()
      self.assertEqual(instance0.sequence,
                       ['/softwareInstanceError'])
      self.assertEqual(instance1.sequence,
                       [ '/stoppedComputerPartition'])

  def test_one_partition_buildout_fail_is_correctly_logged(self):
    """
    1. We set up an instance using a corrupted buildout
    2. It will fail, make sure that whole log is sent to master
    """
    computer = self.getTestComputerClass()(self.software_root, self.instance_root, 1, 1)
    with httmock.HTTMock(computer.request_handler):
      instance = computer.instance_list[0]

      line1 = "Nerdy kitten: Can I haz a process crash?"
      line2 = "Cedric: Sure, here it is."
      instance.software.setBuildout("""#!/bin/sh
echo %s; echo %s; exit 42""" % (line1, line2))
      self.launchSlapgrid()
      self.assertEqual(instance.sequence, ['/softwareInstanceError'])
      # We don't care of actual formatting, we just want to have full log
      self.assertIn(line1, instance.error_log)
      self.assertIn(line2, instance.error_log)
      self.assertIn('Failed to run buildout', instance.error_log)

  def test_processing_summary(self):
    """At the end of instance processing, a summary of partition with errors is displayed.
    """
    computer = self.getTestComputerClass()(self.software_root, self.instance_root, 4, 4)
    _, instance1, instance2, instance3 = computer.instance_list
    # instance0 has no problem, it is not in summary

    # instance 1 fails software
    instance1.software = computer.software_list[1]
    instance1.software.setBuildout("""#!/bin/sh
        echo fake buildout error
        exit 1""")

    # instance 2 fails old style promises
    instance2.requested_state = 'started'
    instance2.setPromise("failing_promise", """#!/bin/sh
        echo héhé fake promise error
        exit 1""")

    # instance 3 fails promise plugin
    instance3.requested_state = 'started'
    instance3.setPluginPromise(
        "failing_promise_plugin.py",
        promise_content="""if 1:
          return self.logger.error("héhé fake promise plugin error")
        """,
    )

    with httmock.HTTMock(computer.request_handler), \
        patch.object(self.grid.logger, 'info',) as dummyLogger, \
        patch.object(self.grid.logger, 'debug',) as unusedLogger:
      self.launchSlapgrid()

    # reconstruct the string like logger does
    self.assertEqual(
        dummyLogger.mock_calls[-5][1][0] % dummyLogger.mock_calls[-5][1][1:],
        'Error while processing the following partitions:')
    self.assertRegex(
        dummyLogger.mock_calls[-4][1][0] % dummyLogger.mock_calls[-4][1][1:],
        r"  1\[\(not ready\)\]: Failed to run buildout profile in directory '.*/instance/1':\nfake buildout error\n\n")
    self.assertEqual(
        dummyLogger.mock_calls[-3][1][0] % dummyLogger.mock_calls[-3][1][1:],
        'Error with promises for the following partitions:')
    self.assertEqual(
        dummyLogger.mock_calls[-2][1][0] % dummyLogger.mock_calls[-2][1][1:],
        "  2[(not ready)]: Promise 'failing_promise' failed with output: héhé fake promise error")
    self.assertEqual(
        dummyLogger.mock_calls[-1][1][0] % dummyLogger.mock_calls[-1][1][1:],
        "  3[(not ready)]: Promise 'failing_promise_plugin.py' failed with output: héhé fake promise plugin error")

  def test_partition_force_stop(self):
    """
    Launch slapgrid with --force-stop:
    - buildout should be processed
    - no timestamp should be generated
    - services should be stopped
    - no report should be sent to master
    """
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    with httmock.HTTMock(computer.request_handler):
      instance = computer.instance_list[0]
      instance.requested_state = 'started'
      instance.timestamp = str(int(time.time()))

      promise_ran = os.path.join(instance.partition_path, 'promise_ran')
      promise = textwrap.dedent("""\
              #!/usr/bin/env sh
              touch "%s"
              exit 127""" % promise_ran)
      instance.setPromise('promise_script', promise)

      self.assertEqual(self.launchSlapgrid(force_stop=True), slapgrid.SLAPGRID_SUCCESS)

      six.assertCountEqual(self,
        os.listdir(instance.partition_path),
        ['etc', '.slapgrid', 'buildout.cfg', 'software_release', 'worked', '.slapos-retention-lock-delay']
      )
      self.assertFalse(os.path.exists(promise_ran))
      self.assertFalse(instance.sequence)

  def test_supervisor_partition_files_removed_on_stop(self):
    computer = self.getTestComputerClass()(self.software_root, self.instance_root, 2, 1)
    with httmock.HTTMock(computer.request_handler):
      for i in range(2):
        instance = computer.instance_list[i]
        instance.requested_state = 'started'
        run_dir = os.path.join(instance.partition_path, 'etc', 'run')
        os.makedirs(run_dir)
        with open(os.path.join(run_dir, 'runner' + str(i)), 'w'): pass
      self.assertEqual(self.launchSlapgrid(), slapgrid.SLAPGRID_SUCCESS)

      conf_path = os.path.join(self.instance_root, 'etc', 'supervisord.conf.d', '%s.conf')
      conf0 = conf_path % 0
      conf1 = conf_path % 1
      for conf in (conf0, conf1):
        self.assertTrue(os.path.exists(conf), conf + ' does not exist')

      computer.instance_list[0].requested_state = 'stopped'
      self.assertEqual(self.launchSlapgrid(), slapgrid.SLAPGRID_SUCCESS)

      self.assertFalse(os.path.exists(conf0), conf0 + ' still exists')
      self.assertTrue(os.path.exists(conf1), conf1 + ' does not exist')

      computer.instance_list[0].requested_state = 'started'
      computer.instance_list[1].requested_state = 'stopped'
      self.assertEqual(self.launchSlapgrid(), slapgrid.SLAPGRID_SUCCESS)

      self.assertTrue(os.path.exists(conf0), conf0 + ' does not exist')
      self.assertFalse(os.path.exists(conf1), conf1 + ' still exists')

      computer.instance_list[0].requested_state = 'stopped'
      computer.instance_list[1].requested_state = 'stopped'
      self.assertEqual(self.launchSlapgrid(), slapgrid.SLAPGRID_SUCCESS)

      for conf in (conf0, conf1):
        self.assertFalse(os.path.exists(conf), conf + ' still exists')

      computer.instance_list[0].requested_state = 'started'
      computer.instance_list[1].requested_state = 'started'
      self.assertEqual(self.launchSlapgrid(), slapgrid.SLAPGRID_SUCCESS)

      for conf in (conf0, conf1):
        self.assertTrue(os.path.exists(conf), conf + ' does not exist')


class TestSlapgridUsageReport(MasterMixin, unittest.TestCase):
  """
  Test suite about slapgrid-ur
  """

  def test_slapgrid_destroys_instance_to_be_destroyed(self):
    """
    Test than an instance in "destroyed" state is correctly destroyed
    """
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    with httmock.HTTMock(computer.request_handler):
      instance = computer.instance_list[0]
      instance.requested_state = 'started'
      instance.software.setBuildout(WRAPPER_CONTENT)
      self.assertEqual(self.grid.processComputerPartitionList(), slapgrid.SLAPGRID_SUCCESS)
      self.assertInstanceDirectoryListEqual(['0'])
      six.assertCountEqual(self, os.listdir(instance.partition_path),
                            ['.slapgrid', '.0_wrapper.log', 'buildout.cfg',
                             'etc', 'software_release', 'worked', '.slapos-retention-lock-delay'])
      wrapper_log = os.path.join(instance.partition_path, '.0_wrapper.log')
      self.assertLogContent(wrapper_log, 'Working')
      six.assertCountEqual(self, os.listdir(self.software_root), [instance.software.software_hash])
      self.assertEqual(computer.sequence,
                       ['/getFullComputerInformation',
                        '/getComputerPartitionCertificate',
                        '/startedComputerPartition'])
      self.assertEqual(instance.state, 'started')

      # Then destroy the instance
      computer.sequence = []
      instance.requested_state = 'destroyed'
      self.assertEqual(self.grid.agregateAndSendUsage(), slapgrid.SLAPGRID_SUCCESS)
      # Assert partition directory is empty
      self.assertInstanceDirectoryListEqual(['0'])
      six.assertCountEqual(self, os.listdir(instance.partition_path), [])
      six.assertCountEqual(self, os.listdir(self.software_root),
                            [instance.software.software_hash])
      # Assert supervisor stopped process
      wrapper_log = os.path.join(instance.partition_path, '.0_wrapper.log')
      self.assertIsNotCreated(wrapper_log)

      self.assertEqual(computer.sequence,
                       ['/getFullComputerInformation',
                        '/getComputerPartitionCertificate',
                        '/stoppedComputerPartition',
                        '/destroyedComputerPartition'])
      self.assertEqual(instance.state, 'destroyed')

  def test_partition_list_is_complete_if_empty_destroyed_partition(self):
    """
    Test that an empty partition with destroyed state but with SR informations
    Is correctly destroyed
    Axiom: each valid partition has a state and a software_release.
    Scenario:
    1. Simulate computer containing one "destroyed" partition but with valid SR
    2. See if it destroyed
    """
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    with httmock.HTTMock(computer.request_handler):
      instance = computer.instance_list[0]

      computer.sequence = []
      instance.requested_state = 'destroyed'
      self.assertEqual(self.grid.agregateAndSendUsage(), slapgrid.SLAPGRID_SUCCESS)
      # Assert partition directory is empty
      self.assertInstanceDirectoryListEqual(['0'])
      six.assertCountEqual(self, os.listdir(instance.partition_path), [])
      six.assertCountEqual(self, os.listdir(self.software_root),
                            [instance.software.software_hash])
      # Assert supervisor stopped process
      wrapper_log = os.path.join(instance.partition_path, '.0_wrapper.log')
      self.assertIsNotCreated(wrapper_log)

      self.assertEqual(
          computer.sequence,
          ['/getFullComputerInformation',
           '/getComputerPartitionCertificate',
           '/stoppedComputerPartition',
           '/destroyedComputerPartition'])

  def test_slapgrid_not_destroy_bad_instance(self):
    """
    Checks that slapgrid-ur don't destroy instance not to be destroyed.
    """
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    with httmock.HTTMock(computer.request_handler):
      instance = computer.instance_list[0]
      instance.requested_state = 'started'
      instance.software.setBuildout(WRAPPER_CONTENT)
      self.assertEqual(self.grid.processComputerPartitionList(), slapgrid.SLAPGRID_SUCCESS)
      self.assertInstanceDirectoryListEqual(['0'])
      six.assertCountEqual(self, os.listdir(instance.partition_path),
                            ['.slapgrid', '.0_wrapper.log', 'buildout.cfg',
                             'etc', 'software_release', 'worked', '.slapos-retention-lock-delay'])
      wrapper_log = os.path.join(instance.partition_path, '.0_wrapper.log')
      self.assertLogContent(wrapper_log, 'Working')
      six.assertCountEqual(self, os.listdir(self.software_root), [instance.software.software_hash])
      self.assertEqual(computer.sequence,
                       ['/getFullComputerInformation',
                        '/getComputerPartitionCertificate',
                        '/startedComputerPartition'])
      self.assertEqual('started', instance.state)

      # Then run usage report and see if it is still working
      computer.sequence = []
      self.assertEqual(self.grid.agregateAndSendUsage(), slapgrid.SLAPGRID_SUCCESS)
      # registerComputerPartition will create one more file:
      from slapos.slap.slap import COMPUTER_PARTITION_REQUEST_LIST_TEMPLATE_FILENAME
      request_list_file = COMPUTER_PARTITION_REQUEST_LIST_TEMPLATE_FILENAME % instance.name
      self.assertInstanceDirectoryListEqual(['0'])
      six.assertCountEqual(self, os.listdir(instance.partition_path),
                            ['.slapgrid', '.0_wrapper.log', 'buildout.cfg',
                             'etc', 'software_release', 'worked',
                             '.slapos-retention-lock-delay', request_list_file])
      wrapper_log = os.path.join(instance.partition_path, '.0_wrapper.log')
      self.assertLogContent(wrapper_log, 'Working')
      self.assertInstanceDirectoryListEqual(['0'])
      six.assertCountEqual(self, os.listdir(instance.partition_path),
                            ['.slapgrid', '.0_wrapper.log', 'buildout.cfg',
                             'etc', 'software_release', 'worked',
                             '.slapos-retention-lock-delay', request_list_file])
      wrapper_log = os.path.join(instance.partition_path, '.0_wrapper.log')
      self.assertLogContent(wrapper_log, 'Working')
      self.assertEqual(computer.sequence,
                       ['/getFullComputerInformation'])
      self.assertEqual('started', instance.state)

  def test_slapgrid_instance_ignore_free_instance(self):
    """
    Test than a free instance (so in "destroyed" state, but empty, without
    software_release URI) is ignored by slapgrid-cp.
    """
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    with httmock.HTTMock(computer.request_handler):
      instance = computer.instance_list[0]
      instance.software.name = None

      computer.sequence = []
      instance.requested_state = 'destroyed'
      self.assertEqual(self.grid.processComputerPartitionList(), slapgrid.SLAPGRID_SUCCESS)
      # Assert partition directory is empty
      self.assertInstanceDirectoryListEqual(['0'])
      six.assertCountEqual(self, os.listdir(instance.partition_path), [])
      six.assertCountEqual(self, os.listdir(self.software_root), [instance.software.software_hash])
      self.assertEqual(computer.sequence, ['/getFullComputerInformation'])

  def test_slapgrid_report_ignore_free_instance(self):
    """
    Test than a free instance (so in "destroyed" state, but empty, without
    software_release URI) is ignored by slapgrid-ur.
    """
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    with httmock.HTTMock(computer.request_handler):
      instance = computer.instance_list[0]
      instance.software.name = None

      computer.sequence = []
      instance.requested_state = 'destroyed'
      self.assertEqual(self.grid.agregateAndSendUsage(), slapgrid.SLAPGRID_SUCCESS)
      # Assert partition directory is empty
      self.assertInstanceDirectoryListEqual(['0'])
      six.assertCountEqual(self, os.listdir(instance.partition_path), [])
      six.assertCountEqual(self, os.listdir(self.software_root), [instance.software.software_hash])
      self.assertEqual(computer.sequence, ['/getFullComputerInformation'])


class TestSlapgridSoftwareRelease(MasterMixin, unittest.TestCase):

  def setUp(self):
    MasterMixin.setUp(self)
    self.pwuid_patch = patch.object(pwd, 'getpwuid', new=self.fake_getpwuid)
    self.pwuid_patch.start()

  def tearDown(self):
    self.pwuid_patch.stop()

  def fake_getpwuid(self, uid):
    return pwd.struct_passwd(
        ("fake", "x", uid, uid, "", self.software_root, "/bin/bash")
    )

  fake_waiting_time = 0.05
  def test_one_software_buildout_fail_is_correctly_logged(self):
    """
    1. We set up a software using a corrupted buildout
    2. It will fail, make sure that whole log is sent to master
    """
    computer = self.getTestComputerClass()(self.software_root, self.instance_root, 1, 1)
    with httmock.HTTMock(computer.request_handler):
      software = computer.software_list[0]

      line1 = "Nerdy kitten: Can I haz a process crash?"
      line2 = "Cedric: Sure, here it is."
      software.setBuildout("""#!/bin/sh
echo %s; echo %s; exit 42""" % (line1, line2))
      self.launchSlapgridSoftware()
      self.assertEqual(software.sequence,
                       ['/buildingSoftwareRelease', '/softwareReleaseError'])
      # We don't care of actual formatting, we just want to have full log
      self.assertIn(line1, software.error_log)
      self.assertIn(line2, software.error_log)
      self.assertIn('Failed to run buildout', software.error_log)

  def test_software_install_generate_buildout_cfg_with_shared_part_list(self):
    computer = self.getTestComputerClass()(self.software_root, self.instance_root, 1, 1)
    with httmock.HTTMock(computer.request_handler):
      software = computer.software_list[0]
      # examine the genrated buildout
      software.setBuildout("""#!/bin/sh
        cat buildout.cfg; exit 1""")
      self.launchSlapgridSoftware()
    self.assertIn('shared-part-list = %s' % self.shared_parts_root, software.error_log)

  def test_remove_software(self):
    computer = self.getTestComputerClass()(self.software_root, self.instance_root, 1, 1)
    with httmock.HTTMock(computer.request_handler):
      software = computer.software_list[0]

      software.setBuildout("""#!/bin/sh
mkdir directory
touch directory/file
""")
      self.launchSlapgridSoftware()
      self.assertIn('directory', os.listdir(os.path.join(self.software_root, software.software_hash)))

      software.requested_state = 'destroyed'
      self.launchSlapgridSoftware()
      self.assertEqual(os.listdir(self.software_root), [])

  def test_remove_software_chmod(self):
    # This software is "hard" to remove, as permissions have been changed
    computer = self.getTestComputerClass()(self.software_root, self.instance_root, 1, 1)
    with httmock.HTTMock(computer.request_handler):
      software = computer.software_list[0]

      software.setBuildout("""#!/bin/sh
mkdir directory
touch directory/file
chmod a-rxw directory/file
chmod a-rxw directory
""")
      self.launchSlapgridSoftware()
      self.assertIn('directory', os.listdir(os.path.join(self.software_root, software.software_hash)))

      software.requested_state = 'destroyed'
      self.launchSlapgridSoftware()
      self.assertEqual(os.listdir(self.software_root), [])

  def test_garbage_collect_software(self):
    computer = self.getTestComputerClass()(self.software_root, self.instance_root, 1, 1)
    with httmock.HTTMock(computer.request_handler):
      software = computer.software_list[0]

      self.launchSlapgridSoftware()
      self.assertEqual(os.listdir(self.software_root), [software.software_hash])

      old_software_hash = '00000000000000000000000000000123'
      os.makedirs(os.path.join(self.software_root, old_software_hash))
      with open(os.path.join(self.software_root, old_software_hash, 'buildout.cfg'), 'w') as f:
        f.write('buildout configuration for old software')

      os.makedirs(os.path.join(self.software_root, 'not_a_software'))

      self.launchSlapgridSoftware()
      self.assertEqual(
        sorted(os.listdir(self.software_root)),
        sorted([software.software_hash, 'not_a_software', old_software_hash]))

      self.launchSlapgridSoftware(garbage_collection=True)
      self.assertEqual(
        sorted(os.listdir(self.software_root)),
        sorted([software.software_hash, 'not_a_software']))

  def test_build_software_with_netrc(self):
    computer = self.getTestComputerClass()(self.software_root, self.instance_root, 1, 1)
    netrc_file = os.path.join(self.software_root, '.netrc')

    with open(netrc_file, 'w') as f:
      f.write('machine localhost login foo password bar')
    with open(os.path.join(self.software_root, 'testing'), 'w') as f:
      f.write('this is not buildout home')
    os.chmod(netrc_file, 0o600)
    with httmock.HTTMock(computer.request_handler):
      software = computer.software_list[0]
      software_path = os.path.join(self.software_root, software.software_hash)
      buildout_netrc = os.path.join(software_path, '.netrc')

      command = """#!/bin/sh
# $HOME is different from buildout netrc home location
if [ -s "$HOME/testing" ]; then
  echo "testing file exists"
  exit 1
fi
"""
      software.setBuildout(command)
      self.launchSlapgridSoftware()
      self.assertTrue(os.path.exists(netrc_file))
      self.assertTrue(os.path.exists(buildout_netrc))

      with open(buildout_netrc) as f:
        content = f.read()
        self.assertEqual(content, 'machine localhost login foo password bar')

      completed = os.path.join(software_path, '.completed')
      os.remove(netrc_file)
      # force rerun of software
      os.remove(completed)
      self.launchSlapgridSoftware()
      self.assertFalse(os.path.exists(buildout_netrc))

class SlapgridInitialization(unittest.TestCase):
  """
  "Abstract" class setting setup and teardown for TestSlapgridArgumentTuple
  and TestSlapgridConfigurationFile.
  """

  def setUp(self):
    """
      Create the minimun default argument and configuration.
    """
    self.certificate_repository_path = tempfile.mkdtemp()
    self.fake_file_descriptor = tempfile.NamedTemporaryFile()
    self.slapos_config_descriptor = tempfile.NamedTemporaryFile()
    self.slapos_config_descriptor.write("""
[slapos]
software_root = /opt/slapgrid
instance_root = /srv/slapgrid
master_url = https://slap.vifib.com/
computer_id = your computer id
buildout = /path/to/buildout/binary
""")
    self.slapos_config_descriptor.seek(0)
    self.default_arg_tuple = (
        '--cert_file', self.fake_file_descriptor.name,
        '--key_file', self.fake_file_descriptor.name,
        '--master_ca_file', self.fake_file_descriptor.name,
        '--certificate_repository_path', self.certificate_repository_path,
        '-c', self.slapos_config_descriptor.name, '--now')

    self.signature_key_file_descriptor = tempfile.NamedTemporaryFile()
    self.signature_key_file_descriptor.seek(0)

  def tearDown(self):
    """
      Removing the temp file.
    """
    self.fake_file_descriptor.close()
    self.slapos_config_descriptor.close()
    self.signature_key_file_descriptor.close()
    shutil.rmtree(self.certificate_repository_path, True)


class TestSlapgridCPWithMasterPromise(MasterMixin, unittest.TestCase):
  def test_one_failing_promise(self):
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    with httmock.HTTMock(computer.request_handler):
      instance = computer.instance_list[0]
      instance.requested_state = 'started'
      worked_file = os.path.join(instance.partition_path, 'fail_worked')
      fail = textwrap.dedent("""\
              #!/usr/bin/env sh
              touch "%s"
              exit 127""" % worked_file)
      instance.setPromise('fail', fail)
      self.assertEqual(self.grid.processComputerPartitionList(),
                       slapos.grid.slapgrid.SLAPGRID_PROMISE_FAIL)
      self.assertTrue(os.path.isfile(worked_file))
      self.assertTrue(instance.error)
      self.assertNotEqual('started', instance.state)

  def test_one_succeeding_promise(self):
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    with httmock.HTTMock(computer.request_handler):
      instance = computer.instance_list[0]
      instance.requested_state = 'started'
      worked_file = os.path.join(instance.partition_path, 'succeed_worked')
      succeed = textwrap.dedent("""\
              #!/usr/bin/env sh
              touch "%s"
              exit 0""" % worked_file)
      instance.setPromise('succeed', succeed)
      self.assertEqual(self.grid.processComputerPartitionList(), slapgrid.SLAPGRID_SUCCESS)
      self.assertTrue(os.path.isfile(worked_file))

      self.assertFalse(instance.error)
      self.assertEqual(instance.state, 'started')

  def test_stderr_has_been_sent(self):
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    with httmock.HTTMock(computer.request_handler):
      instance = computer.instance_list[0]

      instance.requested_state = 'started'

      promise_path = os.path.join(instance.partition_path, 'etc', 'promise')
      os.makedirs(promise_path)
      succeed = os.path.join(promise_path, 'stderr_writer')
      worked_file = os.path.join(instance.partition_path, 'stderr_worked')
      with open(succeed, 'w') as f:
        f.write(textwrap.dedent("""\
              #!/usr/bin/env sh
              touch "%s"
              echo 'Error Promise 254554802' 1>&2
              exit 127""" % worked_file))
      os.chmod(succeed, 0o777)
      self.assertEqual(self.grid.processComputerPartitionList(),
                       slapos.grid.slapgrid.SLAPGRID_PROMISE_FAIL)
      self.assertTrue(os.path.isfile(worked_file))

      log_file = '%s/.slapgrid/log/instance.log' % instance.partition_path
      with open(log_file) as f:
        self.assertIn('Error Promise 254554802', f.read())
      self.assertTrue(instance.error)
      self.assertIsNone(instance.state)

  def test_timeout_works(self):
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    with httmock.HTTMock(computer.request_handler):
      instance = computer.instance_list[0]
      instance.requested_state = 'started'

      promise_path = os.path.join(instance.partition_path, 'etc', 'promise')
      os.makedirs(promise_path)
      succeed = os.path.join(promise_path, 'timed_out_promise')
      worked_file = os.path.join(instance.partition_path, 'timed_out_worked')
      with open(succeed, 'w') as f:
        f.write(textwrap.dedent("""\
              #!/usr/bin/env sh
              touch "%s"
              sleep 25
              exit 0""" % worked_file))
      os.chmod(succeed, 0o777)
      self.assertEqual(self.grid.processComputerPartitionList(),
                       slapos.grid.slapgrid.SLAPGRID_PROMISE_FAIL)
      self.assertTrue(os.path.isfile(worked_file))

      self.assertTrue(instance.error)
      self.assertIsNone(instance.state)

  def test_two_succeeding_promises(self):
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    with httmock.HTTMock(computer.request_handler):
      instance = computer.instance_list[0]
      instance.requested_state = 'started'

      for i in range(2):
        worked_file = os.path.join(instance.partition_path, 'succeed_%s_worked' % i)
        succeed = textwrap.dedent("""\
              #!/usr/bin/env sh
              touch "%s"
              exit 0""" % worked_file)
        instance.setPromise('succeed_%s' % i, succeed)

      self.assertEqual(self.grid.processComputerPartitionList(), slapgrid.SLAPGRID_SUCCESS)
      for i in range(2):
        worked_file = os.path.join(instance.partition_path, 'succeed_%s_worked' % i)
        self.assertTrue(os.path.isfile(worked_file))
      self.assertFalse(instance.error)
      self.assertEqual(instance.state, 'started')

  def test_one_succeeding_one_failing_promises(self):
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    with httmock.HTTMock(computer.request_handler):
      instance = computer.instance_list[0]
      instance.requested_state = 'started'

      for i in range(2):
        worked_file = os.path.join(instance.partition_path, 'promise_worked_%d' % i)
        lockfile = os.path.join(instance.partition_path, 'lock')
        promise = textwrap.dedent("""\
                  #!/usr/bin/env sh
                  touch "%(worked_file)s"
                  if [ ! -f %(lockfile)s ]
                  then
                    touch "%(lockfile)s"
                    exit 0
                  else
                    exit 127
                  fi""" % {
            'worked_file': worked_file,
            'lockfile': lockfile
        })
        instance.setPromise('promise_%s' % i, promise)
      self.assertEqual(self.grid.processComputerPartitionList(),
                       slapos.grid.slapgrid.SLAPGRID_PROMISE_FAIL)
      self.assertEqual(instance.error, 1)
      self.assertNotEqual('started', instance.state)

  def test_one_succeeding_one_timing_out_promises(self):
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    with httmock.HTTMock(computer.request_handler):
      instance = computer.instance_list[0]
      instance.requested_state = 'started'
      for i in range(2):
        worked_file = os.path.join(instance.partition_path, 'promise_worked_%d' % i)
        lockfile = os.path.join(instance.partition_path, 'lock')
        promise = textwrap.dedent("""\
                  #!/usr/bin/env sh
                  touch "%(worked_file)s"
                  if [ ! -f %(lockfile)s ]
                  then
                    touch "%(lockfile)s"
                  else
                    sleep 25
                  fi
                  exit 0""" % {
            'worked_file': worked_file,
            'lockfile': lockfile}
        )
        instance.setPromise('promise_%d' % i, promise)

      self.assertEqual(self.grid.processComputerPartitionList(),
                       slapos.grid.slapgrid.SLAPGRID_PROMISE_FAIL)

      self.assertEqual(instance.error, 1)
      self.assertNotEqual(instance.state, 'started')

  def test_promise_run_if_partition_started_fail(self):
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    with httmock.HTTMock(computer.request_handler):
      instance = computer.instance_list[0]
      instance.requested_state = 'started'
      instance.software.setBuildout("""#!/bin/sh
exit 1
""")
      self.assertEqual(self.grid.processComputerPartitionList(),
                       slapos.grid.slapgrid.SLAPGRID_FAIL)
      self.assertInstanceDirectoryListEqual(['0'])
      six.assertCountEqual(self, os.listdir(instance.partition_path),
                            ['.slapgrid', 'buildout.cfg', 'software_release',
                             '.slapgrid-0-error.log'])

      promise_file = os.path.join(instance.partition_path, 'promise_ran')
      promise = textwrap.dedent("""\
              #!/usr/bin/env sh
              touch "%s"
              exit 127""" % promise_file)
      instance.setPromise('promise_script', promise)
      self.assertEqual(self.grid.processComputerPartitionList(),
                       slapos.grid.slapgrid.SLAPGRID_FAIL)
      self.assertTrue(os.path.isfile(promise_file))
      self.assertTrue(instance.error)

  def test_promise_notrun_if_partition_stopped_fail(self):
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    with httmock.HTTMock(computer.request_handler):
      instance = computer.instance_list[0]
      instance.requested_state = 'stopped'
      instance.software.setBuildout("""#!/bin/sh
exit 1
""")
      self.assertEqual(self.grid.processComputerPartitionList(),
                       slapos.grid.slapgrid.SLAPGRID_FAIL)
      self.assertInstanceDirectoryListEqual(['0'])
      six.assertCountEqual(self, os.listdir(instance.partition_path),
                            ['.slapgrid', 'buildout.cfg', 'software_release',
                             '.slapgrid-0-error.log'])

      promise_file = os.path.join(instance.partition_path, 'promise_ran')
      promise = textwrap.dedent("""\
              #!/usr/bin/env sh
              touch "%s"
              exit 127""" % promise_file)
      instance.setPromise('promise_script', promise)
      self.assertEqual(self.grid.processComputerPartitionList(),
                       slapos.grid.slapgrid.SLAPGRID_FAIL)
      self.assertFalse(os.path.exists(promise_file))
      self.assertTrue(instance.error)


class TestSlapgridDestructionLock(MasterMixin, unittest.TestCase):
  def test_retention_lock(self):
    """
    Higher level test about actual retention (or no-retention) of instance
    if specifying a retention lock delay.
    """
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    with httmock.HTTMock(computer.request_handler):
      instance = computer.instance_list[0]
      instance.requested_state = 'started'
      instance.filter_dict = {'retention_delay': 1.0 / (3600 * 24)}
      self.grid.processComputerPartitionList()
      dummy_instance_file_path = os.path.join(instance.partition_path, 'dummy')
      with open(dummy_instance_file_path, 'w') as dummy_instance_file:
        dummy_instance_file.write('dummy')

      self.assertTrue(os.path.exists(os.path.join(
          instance.partition_path,
          slapos.grid.SlapObject.Partition.retention_lock_delay_filename
      )))

      instance.requested_state = 'destroyed'
      self.grid.agregateAndSendUsage()
      self.assertTrue(os.path.exists(dummy_instance_file_path))
      self.assertTrue(os.path.exists(os.path.join(
          instance.partition_path,
          slapos.grid.SlapObject.Partition.retention_lock_date_filename
      )))

      self.grid.agregateAndSendUsage()
      self.assertTrue(os.path.exists(dummy_instance_file_path))

      time.sleep(1)
      self.grid.agregateAndSendUsage()
      self.assertFalse(os.path.exists(dummy_instance_file_path))


class TestSlapgridCPWithFirewall(MasterMixin, unittest.TestCase):

  def setFirewallConfig(self, source_ip=""):

    self.firewall_cmd_add = os.path.join(self._tempdir, 'firewall_cmd_add')
    with open(self.firewall_cmd_add, 'w') as f:
      f.write("""#!/bin/sh
var="$*"
R=$(echo $var | grep "query-rule") > /dev/null
if [ $? -eq 0 ]; then
  echo "no"
  exit 0
fi
R=$(echo $var | grep "add-rule")
if [ $? -eq 0  ]; then
  echo "success"
  exit 0
fi
echo "ERROR: $var"
exit 1
""")

    self.firewall_cmd_remove = os.path.join(self._tempdir, 'firewall_cmd_remove')
    with open(self.firewall_cmd_remove, 'w') as f:
      f.write("""#!/bin/sh
var="$*"
R=$(echo $var | grep "query-rule")
if [ $? -eq 0 ]; then
  echo "yes"
  exit 0
fi
R=$(echo $var | grep "remove-rule")
if [ $? -eq 0 ]; then
  echo "success"
  exit 0
fi
echo "ERROR: $var"
exit 1
""")

    os.chmod(self.firewall_cmd_add, 0o755)
    os.chmod(self.firewall_cmd_remove, 0o755)

    firewall_conf= dict(
      authorized_sources=source_ip,
      firewall_cmd=self.firewall_cmd_add,
      firewall_executable='/bin/echo "service firewall started"',
      reload_config_cmd='/bin/echo "Config reloaded."',
      log_file='fw-log.log',
      testing=True,
    )
    self.grid.firewall_conf = firewall_conf

  def checkRuleFromIpSource(self, ip, accept_ip_list, cmd_list):
    # XXX - rules for one ip contain 2*len(ip_address_list + accept_ip_list) rules ACCEPT and 4 rules REJECT
    num_rules = len(self.ip_address_list) * 2 + len(accept_ip_list) * 2 + 4
    self.assertEqual(len(cmd_list), num_rules)
    base_cmd = '--permanent --direct --add-rule ipv4 filter'

    # Check that there is REJECT rule on INPUT
    rule = '%s INPUT 1000 -d %s -j REJECT' % (base_cmd, ip)
    self.assertIn(rule, cmd_list)

    # Check that there is REJECT rule on FORWARD
    rule = '%s FORWARD 1000 -d %s -j REJECT' % (base_cmd, ip)
    self.assertIn(rule, cmd_list)

    # Check that there is REJECT rule on INPUT, ESTABLISHED,RELATED
    rule = '%s INPUT 900 -d %s -m state --state ESTABLISHED,RELATED -j REJECT' % (base_cmd, ip)
    self.assertIn(rule, cmd_list)

    # Check that there is REJECT rule on FORWARD, ESTABLISHED,RELATED
    rule = '%s FORWARD 900 -d %s -m state --state ESTABLISHED,RELATED -j REJECT' % (base_cmd, ip)
    self.assertIn(rule, cmd_list)

    # Check that there is INPUT ACCEPT on ip_list
    for _, other_ip in self.ip_address_list:
      rule = '%s INPUT 0 -s %s -d %s -j ACCEPT' % (base_cmd, other_ip, ip)
      self.assertIn(rule, cmd_list)
      rule = '%s FORWARD 0 -s %s -d %s -j ACCEPT' % (base_cmd, other_ip, ip)
      self.assertIn(rule, cmd_list)

    # Check that there is FORWARD ACCEPT on ip_list
    for other_ip in accept_ip_list:
      rule = '%s INPUT 0 -s %s -d %s -j ACCEPT' % (base_cmd, other_ip, ip)
      self.assertIn(rule, cmd_list)
      rule = '%s FORWARD 0 -s %s -d %s -j ACCEPT' % (base_cmd, other_ip, ip)
      self.assertIn(rule, cmd_list)

  def checkRuleFromIpSourceReject(self, ip, reject_ip_list, cmd_list):
    # XXX - rules for one ip contain 2 + 2*len(ip_address_list) rules ACCEPT and 4*len(reject_ip_list) rules REJECT
    num_rules = (len(self.ip_address_list) * 2) + (len(reject_ip_list) * 4)
    self.assertEqual(len(cmd_list), num_rules)
    base_cmd = '--permanent --direct --add-rule ipv4 filter'

    # Check that there is ACCEPT rule on INPUT
    #rule = '%s INPUT 0 -d %s -j ACCEPT' % (base_cmd, ip)
    #self.assertIn(rule, cmd_list)

    # Check that there is ACCEPT rule on FORWARD
    #rule = '%s FORWARD 0 -d %s -j ACCEPT' % (base_cmd, ip)
    #self.assertIn(rule, cmd_list)

    # Check that there is INPUT/FORWARD ACCEPT on ip_list
    for _, other_ip in self.ip_address_list:
      rule = '%s INPUT 0 -s %s -d %s -j ACCEPT' % (base_cmd, other_ip, ip)
      self.assertIn(rule, cmd_list)
      rule = '%s FORWARD 0 -s %s -d %s -j ACCEPT' % (base_cmd, other_ip, ip)
      self.assertIn(rule, cmd_list)

    # Check that there is INPUT/FORWARD REJECT on ip_list
    for other_ip in reject_ip_list:
      rule = '%s INPUT 900 -s %s -d %s -j REJECT' % (base_cmd, other_ip, ip)
      self.assertIn(rule, cmd_list)
      rule = '%s FORWARD 900 -s %s -d %s -j REJECT' % (base_cmd, other_ip, ip)
      self.assertIn(rule, cmd_list)
      rule = '%s INPUT 800 -s %s -d %s -m state --state ESTABLISHED,RELATED -j REJECT' % (base_cmd, other_ip, ip)
      self.assertIn(rule, cmd_list)
      rule = '%s FORWARD 800 -s %s -d %s -m state --state ESTABLISHED,RELATED -j REJECT' % (base_cmd, other_ip, ip)
      self.assertIn(rule, cmd_list)

  def test_getFirewallRules(self):
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    self.setFirewallConfig()
    self.ip_address_list = computer.ip_address_list
    ip = computer.instance_list[0].full_ip_list[0][1]
    source_ip_list = ['10.32.0.15', '10.32.0.0/8']

    cmd_list = self.grid._getFirewallAcceptRules(ip,
                                [elt[1] for elt in self.ip_address_list],
                                source_ip_list,
                                ip_type='ipv4')
    self.checkRuleFromIpSource(ip, source_ip_list, cmd_list)

    cmd_list = self.grid._getFirewallRejectRules(ip,
                                [elt[1] for elt in self.ip_address_list],
                                source_ip_list,
                                ip_type='ipv4')
    self.checkRuleFromIpSourceReject(ip, source_ip_list, cmd_list)


  def test_checkAddFirewallRules(self):
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    self.setFirewallConfig()
    # For simulate query rule success
    self.grid.firewall_conf['firewall_cmd'] = self.firewall_cmd_add
    self.ip_address_list = computer.ip_address_list
    instance = computer.instance_list[0]
    ip = instance.full_ip_list[0][1]
    name = computer.instance_list[0].name

    cmd_list = self.grid._getFirewallAcceptRules(ip,
                                [elt[1] for elt in self.ip_address_list],
                                [],
                                ip_type='ipv4')
    self.grid._checkAddFirewallRules(name, cmd_list, add=True)

    rules_path = os.path.join(
          instance.partition_path,
          slapos.grid.SlapObject.Partition.partition_firewall_rules_name
      )
    with open(rules_path, 'r') as frules:
      rules_list = json.loads(frules.read())
      self.checkRuleFromIpSource(ip, [], rules_list)

    # Remove all rules
    self.grid.firewall_conf['firewall_cmd'] = self.firewall_cmd_remove
    self.grid._checkAddFirewallRules(name, cmd_list, add=False)
    with open(rules_path, 'r') as frules:
      rules_list = json.loads(frules.read())
      self.assertEqual(rules_list, [])

    # Add one more ip in the authorized list
    self.grid.firewall_conf['firewall_cmd'] = self.firewall_cmd_add
    self.ip_address_list.append(('interface1', '10.0.8.7'))
    cmd_list = self.grid._getFirewallAcceptRules(ip,
                                [elt[1] for elt in self.ip_address_list],
                                [],
                                ip_type='ipv4')

    self.grid._checkAddFirewallRules(name, cmd_list, add=True)
    with open(rules_path, 'r') as frules:
      rules_list = json.loads(frules.read())
      self.checkRuleFromIpSource(ip, [], rules_list)

  def test_partition_no_firewall(self):
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    with httmock.HTTMock(computer.request_handler):
      instance = computer.instance_list[0]
      self.assertEqual(self.grid.processComputerPartitionList(),
                        slapgrid.SLAPGRID_SUCCESS)
      self.assertFalse(os.path.exists(os.path.join(
          instance.partition_path,
          slapos.grid.SlapObject.Partition.partition_firewall_rules_name
      )))

  def test_partition_firewall_restrict(self):
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    self.setFirewallConfig()
    with httmock.HTTMock(computer.request_handler):
      instance = computer.instance_list[0]
      self.assertEqual(self.grid.processComputerPartitionList(), slapgrid.SLAPGRID_SUCCESS)
      self.assertTrue(os.path.exists(os.path.join(
          instance.partition_path,
          slapos.grid.SlapObject.Partition.partition_firewall_rules_name
      )))
      rules_path = os.path.join(
          instance.partition_path,
          slapos.grid.SlapObject.Partition.partition_firewall_rules_name
      )
      self.ip_address_list = computer.ip_address_list
      with open(rules_path, 'r') as frules:
        rules_list = json.loads(frules.read())

      ip = instance.full_ip_list[0][1]
      self.checkRuleFromIpSource(ip, [], rules_list)

  def test_partition_firewall(self):
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    self.setFirewallConfig()
    with httmock.HTTMock(computer.request_handler):
      instance = computer.instance_list[0]
      instance.filter_dict = {'fw_restricted_access': 'off'}
      self.assertEqual(self.grid.processComputerPartitionList(), slapgrid.SLAPGRID_SUCCESS)
      self.assertTrue(os.path.exists(os.path.join(
          instance.partition_path,
          slapos.grid.SlapObject.Partition.partition_firewall_rules_name
      )))
      rules_path = os.path.join(
          instance.partition_path,
          slapos.grid.SlapObject.Partition.partition_firewall_rules_name
      )
      self.ip_address_list = computer.ip_address_list
      with open(rules_path, 'r') as frules:
        rules_list = json.loads(frules.read())

      ip = instance.full_ip_list[0][1]
      self.checkRuleFromIpSourceReject(ip, [], rules_list)

  @unittest.skip('Always fail: instance.filter_dict can\'t change')
  def test_partition_firewall_restricted_access_change(self):
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    self.setFirewallConfig()
    with httmock.HTTMock(computer.request_handler):
      instance = computer.instance_list[0]
      instance.filter_dict = {'fw_restricted_access': 'off',
                              'fw_rejected_sources': '10.0.8.11'}
      self.assertEqual(self.grid.processComputerPartitionList(), slapgrid.SLAPGRID_SUCCESS)
      self.assertTrue(os.path.exists(os.path.join(
          instance.partition_path,
          slapos.grid.SlapObject.Partition.partition_firewall_rules_name
      )))
      rules_path = os.path.join(
          instance.partition_path,
          slapos.grid.SlapObject.Partition.partition_firewall_rules_name
      )
      self.ip_address_list = computer.ip_address_list
      with open(rules_path, 'r') as frules:
        rules_list = json.loads(frules.read())

      ip = instance.full_ip_list[0][1]
      self.checkRuleFromIpSourceReject(ip, ['10.0.8.11'], rules_list)

      # For remove rules
      self.grid.firewall_conf['firewall_cmd'] = self.firewall_cmd_remove
      instance.setFilterParameter({'fw_restricted_access': 'on',
                              'fw_authorized_sources': ''})
      self.assertEqual(self.grid.processComputerPartitionList(), slapgrid.SLAPGRID_SUCCESS)

      with open(rules_path, 'r') as frules:
        rules_list = json.loads(frules.read())

      self.checkRuleFromIpSource(ip, [], rules_list)

  def test_partition_firewall_ipsource_accept(self):
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    self.setFirewallConfig()
    source_ip = ['10.0.8.10', '10.0.8.11']
    self.grid.firewall_conf['authorized_sources'] = [source_ip[0]]
    with httmock.HTTMock(computer.request_handler):
      instance = computer.instance_list[0]
      instance.filter_dict = {'fw_restricted_access': 'on',
                              'fw_authorized_sources': source_ip[1]}
      self.assertEqual(self.grid.processComputerPartitionList(), slapgrid.SLAPGRID_SUCCESS)
      self.assertTrue(os.path.exists(os.path.join(
          instance.partition_path,
          slapos.grid.SlapObject.Partition.partition_firewall_rules_name
      )))
      rules_path = os.path.join(
          instance.partition_path,
          slapos.grid.SlapObject.Partition.partition_firewall_rules_name
      )
      rules_list= []
      self.ip_address_list = computer.ip_address_list
      ip = instance.full_ip_list[0][1]
      base_cmd = '--permanent --direct --add-rule ipv4 filter'
      with open(rules_path, 'r') as frules:
        rules_list = json.loads(frules.read())

      for thier_ip in source_ip:
        rule_input = '%s INPUT 0 -s %s -d %s -j ACCEPT' % (base_cmd, thier_ip, ip)
        self.assertIn(rule_input, rules_list)

        rule_fwd = '%s FORWARD 0 -s %s -d %s -j ACCEPT' % (base_cmd, thier_ip, ip)
        self.assertIn(rule_fwd, rules_list)

      self.checkRuleFromIpSource(ip, source_ip, rules_list)

  def test_partition_firewall_ipsource_reject(self):
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    self.setFirewallConfig()
    source_ip = '10.0.8.10'

    self.grid.firewall_conf['authorized_sources'] = ['10.0.8.15']
    with httmock.HTTMock(computer.request_handler):
      instance = computer.instance_list[0]
      instance.filter_dict = {'fw_rejected_sources': source_ip,
                              'fw_restricted_access': 'off'}
      self.assertEqual(self.grid.processComputerPartitionList(), slapgrid.SLAPGRID_SUCCESS)
      self.assertTrue(os.path.exists(os.path.join(
          instance.partition_path,
          slapos.grid.SlapObject.Partition.partition_firewall_rules_name
      )))
      rules_path = os.path.join(
          instance.partition_path,
          slapos.grid.SlapObject.Partition.partition_firewall_rules_name
      )
      rules_list= []
      self.ip_address_list = computer.ip_address_list
      self.ip_address_list.append(('iface', '10.0.8.15'))
      ip = instance.full_ip_list[0][1]
      base_cmd = '--permanent --direct --add-rule ipv4 filter'
      with open(rules_path, 'r') as frules:
        rules_list = json.loads(frules.read())

      self.checkRuleFromIpSourceReject(ip, source_ip.split(' '), rules_list)

  def test_partition_firewall_ip_change(self):
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    self.setFirewallConfig()
    source_ip = ['10.0.8.10', '10.0.8.11']
    self.grid.firewall_conf['authorized_sources'] = [source_ip[0]]
    with httmock.HTTMock(computer.request_handler):
      instance = computer.instance_list[0]
      instance.filter_dict = {'fw_restricted_access': 'on',
                              'fw_authorized_sources': source_ip[1]}
      self.assertEqual(self.grid.processComputerPartitionList(), slapgrid.SLAPGRID_SUCCESS)
      self.assertTrue(os.path.exists(os.path.join(
          instance.partition_path,
          slapos.grid.SlapObject.Partition.partition_firewall_rules_name
      )))
      rules_path = os.path.join(
          instance.partition_path,
          slapos.grid.SlapObject.Partition.partition_firewall_rules_name
      )
      rules_list= []
      self.ip_address_list = computer.ip_address_list
      ip = instance.full_ip_list[0][1]
      with open(rules_path, 'r') as frules:
        rules_list = json.loads(frules.read())

      self.checkRuleFromIpSource(ip, source_ip, rules_list)
      instance = computer.instance_list[0]
      # XXX -- removed
      #instance.filter_dict = {'fw_restricted_access': 'on',
      #                        'fw_authorized_sources': source_ip[0]}

      # For simulate query rule exist
      self.grid.firewall_conf['firewall_cmd'] = self.firewall_cmd_remove
      self.grid.firewall_conf['authorized_sources'] = []
      computer.ip_address_list.append(('route_interface1', '10.10.8.4'))
      self.assertEqual(self.grid.processComputerPartitionList(), slapgrid.SLAPGRID_SUCCESS)
      self.ip_address_list = computer.ip_address_list

      with open(rules_path, 'r') as frules:
        rules_list = json.loads(frules.read())
      self.checkRuleFromIpSource(ip, [source_ip[1]], rules_list)

class TestSlapgridCPWithTransaction(MasterMixin, unittest.TestCase):

  def test_one_partition(self):
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    with httmock.HTTMock(computer.request_handler):
      instance = computer.instance_list[0]
      partition = os.path.join(self.instance_root, '0')
      request_list_file = os.path.join(partition,
          COMPUTER_PARTITION_REQUEST_LIST_TEMPLATE_FILENAME % instance.name)
      with open(request_list_file, 'w') as f:
        f.write('some partition')
      self.assertEqual(self.grid.processComputerPartitionList(), slapgrid.SLAPGRID_SUCCESS)
      self.assertInstanceDirectoryListEqual(['0'])

      self.assertFalse(os.path.exists(request_list_file))

class TestSlapgridReportWithPreDeleteScript(MasterMixin, unittest.TestCase):

  prerm_script_content = """#!/bin/sh

echo "Running prerm script for this partition..."
touch etc/prerm.txt
for i in {1..2}
do
  echo "sleeping for 1s..."
  sleep 1
done
echo "finished prerm script."
rm etc/prerm.txt

exit 0
"""

  def _wait_prerm_script_finished(self, base_path):
    check_file = os.path.join(base_path, 'etc/prerm.txt')
    limit = 10
    count = 0
    time.sleep(1)
    while (count < limit) and os.path.exists(check_file):
      time.sleep(1)
      count += 1

  def test_partition_destroy_with_pre_remove_service(self):
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    with httmock.HTTMock(computer.request_handler):
      partition = computer.instance_list[0]
      pre_delete_dir = os.path.join(partition.partition_path, 'etc/prerm')
      pre_delete_script = os.path.join(pre_delete_dir, 'slapos_pre_delete')
      partition.requested_state = 'started'
      partition.software.setBuildout(WRAPPER_CONTENT)
      self.assertEqual(self.grid.processComputerPartitionList(), slapgrid.SLAPGRID_SUCCESS)
      os.makedirs(pre_delete_dir, 0o700)
      with open(pre_delete_script, 'w') as f:
        f.write(self.prerm_script_content)
      os.chmod(pre_delete_script, 0o754)
      self.assertInstanceDirectoryListEqual(['0'])
      six.assertCountEqual(self, os.listdir(partition.partition_path),
                            ['.slapgrid', '.0_wrapper.log', 'buildout.cfg',
                             'etc', 'software_release', 'worked', '.slapos-retention-lock-delay'])
      self.assertEqual(computer.sequence,
                       ['/getFullComputerInformation',
                        '/getComputerPartitionCertificate',
                        '/startedComputerPartition'])
      self.assertEqual(partition.state, 'started')
      manager_list = slapmanager.from_config({'manager_list': 'prerm'})
      self.grid._manager_list = manager_list

      partition.requested_state = 'destroyed'
      self.assertEqual(self.grid.agregateAndSendUsage(), slapgrid.SLAPGRID_SUCCESS)
      # Assert partition directory is not destroyed (pre-delete is running)
      self.assertInstanceDirectoryListEqual(['0'])
      six.assertCountEqual(self, os.listdir(partition.partition_path),
                            ['.slapgrid', '.0_wrapper.log', 'buildout.cfg',
                             'etc', 'software_release', 'worked', '.slapos-retention-lock-delay',
                             '.0-prerm_slapos_pre_delete.log', '.slapos-report-wait-service-list',
                             '.slapos-request-transaction-0'])
      six.assertCountEqual(self, os.listdir(self.software_root),
                            [partition.software.software_hash])

      # wait until the pre-delete script is finished
      self._wait_prerm_script_finished(partition.partition_path)

      self.assertEqual(self.grid.agregateAndSendUsage(), slapgrid.SLAPGRID_SUCCESS)
      # Assert partition directory is empty
      self.assertInstanceDirectoryListEqual(['0'])
      six.assertCountEqual(self, os.listdir(partition.partition_path), [])

  def test_partition_destroy_pre_remove_with_retention_lock(self):
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    with httmock.HTTMock(computer.request_handler):
      partition = computer.instance_list[0]
      pre_delete_dir = os.path.join(partition.partition_path, 'etc/prerm')
      pre_delete_script = os.path.join(pre_delete_dir, 'slapos_pre_delete')
      partition.requested_state = 'started'
      partition.filter_dict = {'retention_delay': 1.0 / (3600 * 24)}

      self.assertEqual(self.grid.processComputerPartitionList(), slapgrid.SLAPGRID_SUCCESS)
      self.assertTrue(os.path.exists(os.path.join(
          partition.partition_path,
          slapos.grid.SlapObject.Partition.retention_lock_delay_filename
      )))

      os.makedirs(pre_delete_dir, 0o700)
      with open(pre_delete_script, 'w') as f:
        f.write(self.prerm_script_content)
      os.chmod(pre_delete_script, 0o754)
      self.assertTrue(os.path.exists(pre_delete_script))

      manager_list = slapmanager.from_config({'manager_list': 'prerm'})
      self.grid._manager_list = manager_list

      partition.requested_state = 'destroyed'
      self.assertEqual(self.grid.agregateAndSendUsage(), slapgrid.SLAPGRID_SUCCESS)
      # Assert partition directory is not destroyed (retention-delay-lock)
      six.assertCountEqual(self, os.listdir(partition.partition_path),
                            ['.slapgrid', 'buildout.cfg', 'etc', 'software_release',
                             'worked', '.slapos-retention-lock-delay',
                             '.slapos-retention-lock-date', '.slapos-request-transaction-0'])
      self.assertTrue(os.path.exists(pre_delete_script))
      self.assertTrue(os.path.exists(os.path.join(
          partition.partition_path,
          slapos.grid.SlapObject.Partition.retention_lock_date_filename
      )))

      time.sleep(1)
      self.assertEqual(self.grid.agregateAndSendUsage(), slapgrid.SLAPGRID_SUCCESS)

      # Assert partition directory is not destroyed (pre-delete is running)
      six.assertCountEqual(self, os.listdir(partition.partition_path),
                            ['.slapgrid', 'buildout.cfg', 'etc', 'software_release',
                             'worked', '.slapos-retention-lock-delay', '.slapos-retention-lock-date',
                             '.0-prerm_slapos_pre_delete.log', '.slapos-report-wait-service-list',
                             '.slapos-request-transaction-0'])

      # wait until the pre-delete script is finished
      self._wait_prerm_script_finished(partition.partition_path)

      self.assertEqual(self.grid.agregateAndSendUsage(), slapgrid.SLAPGRID_SUCCESS)
      # Assert partition directory is empty
      six.assertCountEqual(self, os.listdir(partition.partition_path), [])

  def test_partition_destroy_pre_remove_script_not_stopped(self):
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    with httmock.HTTMock(computer.request_handler):
      partition = computer.instance_list[0]
      pre_delete_dir = os.path.join(partition.partition_path, 'etc/prerm')
      pre_delete_script = os.path.join(pre_delete_dir, 'slapos_pre_delete')
      partition.requested_state = 'started'
      self.assertEqual(self.grid.processComputerPartitionList(), slapgrid.SLAPGRID_SUCCESS)
      os.makedirs(pre_delete_dir, 0o700)
      with open(pre_delete_script, 'w') as f:
        f.write(self.prerm_script_content)
      os.chmod(pre_delete_script, 0o754)
      self.assertEqual(partition.state, 'started')
      manager_list = slapmanager.from_config({'manager_list': 'prerm'})
      self.grid._manager_list = manager_list

      partition.requested_state = 'destroyed'
      self.assertEqual(self.grid.agregateAndSendUsage(), slapgrid.SLAPGRID_SUCCESS)
      # Assert partition directory is not destroyed (pre-delete is running)
      six.assertCountEqual(self, os.listdir(partition.partition_path),
                            ['.slapgrid', 'buildout.cfg', 'etc', 'software_release',
                             'worked', '.slapos-retention-lock-delay', '.slapos-request-transaction-0',
                             '.0-prerm_slapos_pre_delete.log', '.slapos-report-wait-service-list'])

      # wait until the pre-delete script is finished
      self._wait_prerm_script_finished(partition.partition_path)
      with open(os.path.join(partition.partition_path, '.0-prerm_slapos_pre_delete.log')) as f:
        # the script is well finished...
        self.assertIn("finished prerm script.", f.read())

      self.assertEqual(self.grid.agregateAndSendUsage(), slapgrid.SLAPGRID_SUCCESS)
      # Assert partition directory is empty
      self.assertInstanceDirectoryListEqual(['0'])
      six.assertCountEqual(self, os.listdir(partition.partition_path), [])

  def test_partition_destroy_pre_remove_script_run_as_partition_user(self):
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    with httmock.HTTMock(computer.request_handler):
      partition = computer.instance_list[0]
      pre_delete_dir = os.path.join(partition.partition_path, 'etc/prerm')
      pre_delete_script = os.path.join(pre_delete_dir, 'slapos_pre_delete')
      partition.requested_state = 'started'
      self.assertEqual(self.grid.processComputerPartitionList(), slapgrid.SLAPGRID_SUCCESS)
      os.makedirs(pre_delete_dir, 0o700)
      with open(pre_delete_script, 'w') as f:
        f.write(self.prerm_script_content)
      os.chmod(pre_delete_script, 0o754)

      manager_list = slapmanager.from_config({'manager_list': 'prerm'})
      self.grid._manager_list = manager_list

      partition.requested_state = 'destroyed'
      self.assertEqual(self.grid.agregateAndSendUsage(), slapgrid.SLAPGRID_SUCCESS)
      # Assert partition directory is not destroyed (pre-delete is running)
      six.assertCountEqual(self, os.listdir(partition.partition_path),
                            ['.slapgrid', 'buildout.cfg', 'etc', 'software_release',
                             'worked', '.slapos-retention-lock-delay', '.slapos-request-transaction-0',
                             '.0-prerm_slapos_pre_delete.log', '.slapos-report-wait-service-list'])

      stat_info = os.stat(partition.partition_path)
      uid = stat_info.st_uid
      gid = stat_info.st_gid
      partition_supervisor_conf_file = os.path.join(self.instance_root,
                                          'etc/supervisord.conf.d',
                                          '%s.conf' % partition.name)
      prerm_supervisor_conf_file = os.path.join(self.instance_root,
                                          'etc/supervisord.conf.d',
                                          '%s-prerm.conf' % partition.name)
      self.assertFalse(os.path.exists(partition_supervisor_conf_file))
      self.assertTrue(os.path.exists(prerm_supervisor_conf_file))
      regex_user = r"user=(\d+)"
      regex_group = r"group=(\d+)"
      with open(prerm_supervisor_conf_file) as f:
        config = f.read()
        # search user uid in conf file
        result = re.search(regex_user, config, re.DOTALL)
        self.assertTrue(result is not None)
        self.assertEqual(int(result.groups()[0]), uid)
        # search user group gid in conf file
        result = re.search(regex_group, config, re.DOTALL)
        self.assertTrue(result is not None)
        self.assertEqual(int(result.groups()[0]), gid)

      # wait until the pre-delete script is finished
      self._wait_prerm_script_finished(partition.partition_path)

      self.assertEqual(self.grid.agregateAndSendUsage(), slapgrid.SLAPGRID_SUCCESS)
      # Assert partition directory is empty
      self.assertInstanceDirectoryListEqual(['0'])
      six.assertCountEqual(self, os.listdir(partition.partition_path), [])


# test that slapgrid commands, like e.g. 'slapos node software' do not leak
# file descriptors besides stdin, stdout, stderr to spawned processes.
class TestSlapgridNoFDLeak(MasterMixin, unittest.TestCase):

  def test_no_fd_leak(self):
    filev = []
    try:
      # open some file descriptors
      for i in range(4):
        f = open(os.devnull)
        filev.append(f)
        self.assertGreater(f.fileno(), 2)

      # 'node software' with check that buildout does not see opened files
      self._test_no_fd_leak()

    finally:
      for f in filev:
        f.close()

  def _test_no_fd_leak(self):
    computer = self.getTestComputerClass()(self.software_root, self.instance_root, 1, 1)
    with httmock.HTTMock(computer.request_handler):
      software = computer.software_list[0]

      software.setBuildout("""#!/bin/bash
fdleak() {
  echo "file descriptors: leaked:" "$@"
  exit 1
}

# https://unix.stackexchange.com/a/206848
: >&3 && fdleak 3
: >&4 && fdleak 4
: >&5 && fdleak 5
: >&6 && fdleak 6

echo "file descriptors: ok"
exit 1  # do not proceed trying to use this software
""")

      self.launchSlapgridSoftware()

      self.assertEqual(software.sequence,
                       ['/buildingSoftwareRelease', '/softwareReleaseError'])
      self.assertNotIn("file descriptors: leaked", software.error_log)
      self.assertIn("file descriptors: ok", software.error_log)

class TestSlapgridWithPortRedirection(MasterMixin, unittest.TestCase):

  def setUp(self):
    MasterMixin.setUp(self)
    manager_list = slapmanager.from_config({'manager_list': 'portredir'})
    self.grid._manager_list = manager_list

    self.computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    self.partition = self.computer.instance_list[0]
    self.socat_supervisord_config_path = os.path.join(
      self.instance_root, 'etc/supervisord.conf.d/0-socat.conf')

    self.port_redirect_path = os.path.join(self.partition.partition_path,
                                           slapmanager.portredir.Manager.port_redirect_filename)

  def _mock_requests(self):
    return httmock.HTTMock(self.computer.request_handler)

  def _read_socat_supervisord_config(self):
    with open(self.socat_supervisord_config_path) as f:
      return f.read()

  def _setup_instance(self, config):
    with open(self.port_redirect_path, 'w+') as f:
      json.dump(config, f)

    self.partition.requested_state = 'started'
    self.partition.software.setBuildout(WRAPPER_CONTENT)
    self.assertEqual(self.grid.processComputerPartitionList(), slapgrid.SLAPGRID_SUCCESS)

    self.assertEqual(self.computer.sequence,
                     ['/getFullComputerInformation',
                      '/getComputerPartitionCertificate',
                      '/startedComputerPartition'])
    self.assertEqual(self.partition.state, 'started')

  def test_simple_port_redirection(self):
    with self._mock_requests():
      self._setup_instance([
        {
          'srcPort': 1234,
          'destPort': 4321,
          'destAddress': '127.0.0.1',
        }
      ])

      # Check the socat command
      socat_supervisord_config = self._read_socat_supervisord_config()
      self.assertIn('socat-tcp-{}'.format(1234), socat_supervisord_config)
      self.assertIn('socat TCP4-LISTEN:1234,fork TCP4:127.0.0.1:4321', socat_supervisord_config)

  def test_ipv6_port_redirection(self):
    with self._mock_requests():
      self._setup_instance([
        {
          'srcPort': 1234,
          'destPort': 4321,
          'destAddress': '::1',
        }
      ])

      # Check the socat command
      socat_supervisord_config = self._read_socat_supervisord_config()
      self.assertIn('socat-tcp-{}'.format(1234), socat_supervisord_config)
      self.assertIn('socat TCP4-LISTEN:1234,fork TCP6:[::1]:4321', socat_supervisord_config)

  def test_udp_port_redirection(self):
    with self._mock_requests():
      self._setup_instance([
        {
          'type': 'udp',
          'srcPort': 1234,
          'destPort': 4321,
          'destAddress': '127.0.0.1',
        }
      ])

      # Check the socat command
      socat_supervisord_config = self._read_socat_supervisord_config()
      self.assertIn('socat-udp-{}'.format(1234), socat_supervisord_config)
      self.assertIn('socat UDP4-LISTEN:1234,fork UDP4:127.0.0.1:4321', socat_supervisord_config)

  def test_portredir_config_change(self):
    # We want the partition to just get updated, not recreated
    self.partition.timestamp = str(int(time.time()))

    with self._mock_requests():
      self._setup_instance([
        {
          'srcPort': 1234,
          'destPort': 4321,
          'destAddress': '127.0.0.1',
        },
      ])

      # Check the socat command
      socat_supervisord_config = self._read_socat_supervisord_config()
      self.assertIn('socat-tcp-{}'.format(1234), socat_supervisord_config)
      self.assertIn('socat TCP4-LISTEN:1234,fork TCP4:127.0.0.1:4321', socat_supervisord_config)

      # Remove the port binding from config
      with open(self.port_redirect_path, 'w+') as f:
        json.dump([], f)

      self.assertEqual(self.grid.processComputerPartitionList(), slapgrid.SLAPGRID_SUCCESS)

      self.assertEqual(self.computer.sequence,
                       ['/getFullComputerInformation',
                        '/getComputerPartitionCertificate',
                        '/startedComputerPartition',
                        '/getComputerPartitionCertificate',
                        '/startedComputerPartition'])
      self.assertEqual(self.partition.state, 'started')

      # Check the socat command
      self.assertFalse(os.path.exists(self.socat_supervisord_config_path))

  def test_port_redirection_config_bad_source_port(self):
    with self._mock_requests():
      self._setup_instance([
        {
          'srcPort': 'bad',
          'destPort': 4321,
          'destAddress': '127.0.0.1',
        },
      ])

      # Check the socat command
      self.assertFalse(os.path.exists(self.socat_supervisord_config_path))

  def test_port_redirection_config_bad_dest_port(self):
    with self._mock_requests():
      self._setup_instance([
        {
          'srcPort': 1234,
          'destPort': 'wolf',
          'destAddress': '127.0.0.1',
        },
      ])

      # Check the socat command
      self.assertFalse(os.path.exists(self.socat_supervisord_config_path))

  def test_port_redirection_config_bad_source_address(self):
    with self._mock_requests():
      self._setup_instance([
        {
          'srcPort': 1234,
          'srcAddress': 'bad',
          'destPort': 4321,
          'destAddress': '127.0.0.1',
        },
      ])

      # Check the socat command
      self.assertFalse(os.path.exists(self.socat_supervisord_config_path))

  def test_port_redirection_config_bad_dest_address(self):
    with self._mock_requests():
      self._setup_instance([
        {
          'srcPort': 1234,
          'destPort': 4321,
          'destAddress': 'wolf',
        },
      ])

      # Check the socat command
      self.assertFalse(os.path.exists(self.socat_supervisord_config_path))

  def test_port_redirection_config_bad_redir_type(self):
    with self._mock_requests():
      self._setup_instance([
        {
          'type': 'htcpcp',
          'srcPort': 1234,
          'destPort': 4321,
          'destAddress': '127.0.0.1',
        },
      ])

      # Check the socat command
      self.assertFalse(os.path.exists(self.socat_supervisord_config_path))


class TestSlapgridWithDevPermLsblk(MasterMixin, unittest.TestCase):
  config = {'manager_list': 'devperm'}

  def _getLsblkJsonDict(self):
    return {
      "blockdevices": [{
        "path": "/dev/tst",
        "type": "disk",
        "children": [{
          "path": "/dev/toolong",
          "type": "part"
        }]
      }]
    }

  def setUpExpected(self):
    gid = grp.getgrnam("disk").gr_gid
    uid = os.stat(os.environ['HOME']).st_uid
    self.test_os_chown_call_list = [
      ['/dev/tst', uid, gid],
      ['/dev/tst', uid, gid],
    ]
    self.test_link_os_chown_call_list = [
      ['/dev/tst', uid, gid],
      ['/dev/tst', uid, gid],
    ]
    self.test_link_os_chown_call_list_long = [
      ['/dev/toolong', uid, gid],
      ['/dev/toolong', uid, gid],
    ]

  def setUp(self):
    self.setUpExpected()
    self.os_chown_call_list = []
    MasterMixin.setUp(self)
    manager_list = slapmanager.from_config(self.config)
    self.grid._manager_list = manager_list

    self.computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    self.partition = self.computer.instance_list[0]
    self.instance_supervisord_config_path = os.path.join(
      self.instance_root, 'etc/supervisord.conf.d/0.conf')

    self.disk_device_filename = os.path.join(
      self.partition.partition_path,
      slapmanager.devperm.Manager.disk_device_filename)
    self.patcher_list = [
      patch.object(os.path, 'exists', new=self.os_path_exists),
      patch.object(os, 'stat', new=self.os_stat),
      patch.object(os, 'chown', new=self.os_chown),
      patch.object(slapmanager.devperm.Manager, '_getLsblkJsonDict', new=self._getLsblkJsonDict)
    ]
    [q.start() for q in self.patcher_list]

  def tearDown(self):
    [q.stop() for q in self.patcher_list]

  def _mock_requests(self):
    return httmock.HTTMock(self.computer.request_handler)

  def os_path_exists(self, path, original=os.path.exists):
    if path in ['/dev/tst', '/dev/toolong']:
      return True
    elif path == '/dev/non':
      return False
    else:
      return original(path)

  def os_stat(self, path, original=os.stat):
    if path in ['/dev/tst', '/dev/toolong']:
      class dummy():
        pass
      mocked = dummy()
      mocked.st_uid = original(os.environ['HOME']).st_uid + 1
      return mocked
    else:
      return original(path)

  def os_chown(self, path, uid, gid, original=os.chown):
    if path.startswith('/dev/tst') or path.startswith('/dev/toolong'):
      self.os_chown_call_list.append([path, uid, gid])
      return
    else:
      original(path, uid, gid)

  def test(self):
    with self._mock_requests():
      with open(self.disk_device_filename, 'w+') as f:
        json.dump([{'disk': '/dev/tst'}], f)

      self.partition.requested_state = 'started'
      self.partition.software.setBuildout(WRAPPER_CONTENT)

      self.assertEqual(self.grid.processComputerPartitionList(), slapgrid.SLAPGRID_SUCCESS)

      self.assertEqual(
        self.os_chown_call_list,
        self.test_os_chown_call_list
      )

  def test_link(self):
    temp_dir = tempfile.mkdtemp()
    self.addCleanup(shutil.rmtree, temp_dir)
    os.symlink('/dev/tst', os.path.join(temp_dir, 'some_link'))
    with self._mock_requests():
      with open(self.disk_device_filename, 'w+') as f:
        json.dump([{'disk': os.path.join(temp_dir, 'some_link')}], f)

      self.partition.requested_state = 'started'
      self.partition.software.setBuildout(WRAPPER_CONTENT)

      self.assertEqual(self.grid.processComputerPartitionList(), slapgrid.SLAPGRID_SUCCESS)

      self.assertEqual(
        self.os_chown_call_list,
        self.test_link_os_chown_call_list
      )

  def test_bad_link(self):
    temp_dir = tempfile.mkdtemp()
    self.addCleanup(shutil.rmtree, temp_dir)
    os.symlink('/dev/non', os.path.join(temp_dir, 'bad_link'))
    with self._mock_requests():
      with open(self.disk_device_filename, 'w+') as f:
        json.dump([{'disk': os.path.join(temp_dir, 'bad_link')}], f)

      self.partition.requested_state = 'started'
      self.partition.software.setBuildout(WRAPPER_CONTENT)

      self.assertEqual(self.grid.processComputerPartitionList(), slapgrid.SLAPGRID_SUCCESS)

      self.assertEqual(
        self.os_chown_call_list,
        []
      )

  def test_long(self):
    with self._mock_requests():
      with open(self.disk_device_filename, 'w+') as f:
        json.dump([{'disk': '/dev/toolong'}], f)

      self.partition.requested_state = 'started'
      self.partition.software.setBuildout(WRAPPER_CONTENT)

      self.assertEqual(self.grid.processComputerPartitionList(), slapgrid.SLAPGRID_SUCCESS)

      self.assertEqual(
        self.os_chown_call_list,
        self.test_link_os_chown_call_list_long
      )

  def test_not_existing(self):
    with self._mock_requests():
      with open(self.disk_device_filename, 'w+') as f:
        json.dump([{'disk': '/dev/non'}], f)

      self.partition.requested_state = 'started'
      self.partition.software.setBuildout(WRAPPER_CONTENT)

      self.assertEqual(self.grid.processComputerPartitionList(), slapgrid.SLAPGRID_SUCCESS)

      self.assertEqual(
        self.os_chown_call_list,
        []
      )


class TestSlapgridWithDevPermManagerDevPermEmptyLsblk(TestSlapgridWithDevPermLsblk):
  config = {
    'manager_list': 'devperm',
    'manager': {'devperm': {}}
  }


class TestSlapgridWithDevPermManagerDevPermListEmptyLsblk(TestSlapgridWithDevPermLsblk):
  config = {
    'manager_list': 'devperm',
    'manager': {'devperm': {'allowed-disk-for-vm': ''}}
  }
  def setUpExpected(self):
    self.test_os_chown_call_list = [
    ]
    self.test_link_os_chown_call_list = [
    ]
    self.test_link_os_chown_call_list_long = [
    ]


class TestSlapgridWithDevPermManagerDevPermDisallowLsblk(TestSlapgridWithDevPermLsblk):
  config = {
    'manager_list': 'devperm',
    'manager': {'devperm': {'allowed-disk-for-vm': '/dev/quo'}}
  }
  def setUpExpected(self):
    self.test_os_chown_call_list = [
    ]
    self.test_link_os_chown_call_list = [
    ]
    self.test_link_os_chown_call_list_long = [
    ]


class TestSlapgridWithDevPermManagerDevPermAllowLsblk(TestSlapgridWithDevPermLsblk):
  config = {
    'manager_list': 'devperm',
    'manager': {'devperm': {'allowed-disk-for-vm': '/dev/tst'}}
  }
  def setUpExpected(self):
    gid = grp.getgrnam("disk").gr_gid
    uid = os.stat(os.environ['HOME']).st_uid
    self.test_os_chown_call_list = [
      ['/dev/tst', uid, gid],
      ['/dev/tst', uid, gid],
    ]
    self.test_link_os_chown_call_list = [
      ['/dev/tst', uid, gid],
      ['/dev/tst', uid, gid],
    ]
    self.test_link_os_chown_call_list_long = [
    ]


class TestSlapgridWithWhitelistfirewall(MasterMixin, unittest.TestCase):
  config = {
    'manager_list': 'whitelistfirewall',
    'firewall': {
      'firewall_cmd': 'firewall_cmd',
    }
  }

  def setUp(self):
    MasterMixin.setUp(self)
    self.uid_owner = str(os.stat(os.environ['HOME']).st_uid)
    manager_list = slapmanager.from_config(self.config)
    self.grid._manager_list = manager_list

    self.computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    self.partition = self.computer.instance_list[0]

    self.whitelist_firewall_filename = os.path.join(
      self.partition.partition_path,
      slapmanager.whitelistfirewall.Manager.whitelist_firewall_filename)

    self.whitelist_firewall_md5sum = os.path.join(
      self.partition.partition_path,
      slapmanager.whitelistfirewall.Manager.whitelist_firewall_md5sum)

    self.fexecute_call_list = []
    self.fexecute_side_effect = {}
    self.fexecute_returncode = 0
    self.fexecute_result = ''
    self.patcher_list = [
      patch.object(slapmanager.whitelistfirewall, 'fexecute', new=self.fexecute)
    ]
    [q.start() for q in self.patcher_list]

  def fexecute(self, arg_list):
    self.fexecute_call_list.append(arg_list)
    return self.fexecute_side_effect.get(str(arg_list), (0, ''))

  def tearDown(self):
    [q.stop() for q in self.patcher_list]

  def _mock_requests(self):
    return httmock.HTTMock(self.computer.request_handler)

  def test(self):
    with self._mock_requests():
      with open(self.whitelist_firewall_filename, 'w+') as f:
        json.dump(['127.0.0.1'], f)

      self.partition.requested_state = 'started'
      self.partition.software.setBuildout(WRAPPER_CONTENT)

      self.assertEqual(self.grid.processComputerPartitionList(), slapgrid.SLAPGRID_SUCCESS)

      query_chain = ['firewall_cmd', '--direct', '--permanent', '--query-chain', 'ipv4', 'filter', '0-whitelist']
      query_owner_rule = ['firewall_cmd', '--direct', '--permanent', '--query-rule', 'ipv4', 'filter', 'OUTPUT', '0', '-m', 'owner', '--uid-owner', self.uid_owner, '-j', '0-whitelist']
      self.assertEqual(
        self.fexecute_call_list,
        [
          query_chain,
          ['firewall_cmd', '--direct', '--permanent', '--add-chain', 'ipv4', 'filter', '0-whitelist'],
          ['firewall_cmd', '--direct', '--permanent', '--remove-rules', 'ipv4', 'filter', '0-whitelist'],
          ['firewall_cmd', '--direct', '--permanent', '--add-rule', 'ipv4', 'filter', '0-whitelist', '0', '-d', u'127.0.0.1', '-j', 'ACCEPT'],
          ['firewall_cmd', '--direct', '--permanent', '--add-rule', 'ipv4', 'filter', '0-whitelist', '0', '-j', 'REJECT'],
          query_owner_rule,
          ['firewall_cmd', '--direct', '--permanent', '--add-rule', 'ipv4', 'filter', 'OUTPUT', '0', '-m', 'owner', '--uid-owner', self.uid_owner, '-j', '0-whitelist'],
          ['firewall_cmd', '--reload']
        ]
      )
      with open(self.whitelist_firewall_filename, 'rb') as fh:
        expected_md5sum = hashlib.md5(fh.read().strip()).hexdigest()
      try:
        with open(self.whitelist_firewall_md5sum, 'rb') as fh:
          got_md5sum = fh.read().strip().decode("utf-8")
      except Exception:
        got_md5sum = None
      self.assertEqual(expected_md5sum, got_md5sum)


      # check no-op behaviour
      self.fexecute_call_list = []
      self.fexecute_side_effect[str(query_chain)] = (0, 'yes')
      self.fexecute_side_effect[str(query_owner_rule)] = (0, 'yes')
      self.partition.requested_state = 'started'
      self.partition.software.setBuildout(WRAPPER_CONTENT)

      self.assertEqual(self.grid.processComputerPartitionList(), slapgrid.SLAPGRID_SUCCESS)

      self.assertEqual(
        self.fexecute_call_list,
        [
          query_chain
        ]
      )

      # check update
      self.fexecute_call_list = []
      self.fexecute_side_effect[str(query_chain)] = (0, 'yes')
      self.fexecute_side_effect[str(query_owner_rule)] = (0, 'yes')
      with open(self.whitelist_firewall_filename, 'w+') as f:
        json.dump(['127.0.0.1', '127.0.0.2'], f)
      self.partition.requested_state = 'started'
      self.partition.software.setBuildout(WRAPPER_CONTENT)

      self.assertEqual(self.grid.processComputerPartitionList(), slapgrid.SLAPGRID_SUCCESS)

      self.assertEqual(
        self.fexecute_call_list,
        [
          query_chain,
          ['firewall_cmd', '--direct', '--permanent', '--remove-rules', 'ipv4', 'filter', '0-whitelist'],
          ['firewall_cmd', '--direct', '--permanent', '--add-rule', 'ipv4', 'filter', '0-whitelist', '0', '-d', '127.0.0.1', '-j', 'ACCEPT'],
          ['firewall_cmd', '--direct', '--permanent', '--add-rule', 'ipv4', 'filter', '0-whitelist', '0', '-d', '127.0.0.2', '-j', 'ACCEPT'],
          ['firewall_cmd', '--direct', '--permanent', '--add-rule', 'ipv4', 'filter', '0-whitelist', '0', '-j', 'REJECT'],
          query_owner_rule,
          ['firewall_cmd', '--reload']]
      )

      # check behaviour after removing the configuration file
      os.unlink(self.whitelist_firewall_filename)
      # reset previous calls
      self.fexecute_call_list = []
      # setup side effects
      self.fexecute_side_effect[str(query_chain)] = (0, 'yes')
      self.fexecute_side_effect[str(query_owner_rule)] = (0, 'yes')
      self.partition.requested_state = 'started'
      self.partition.software.setBuildout(WRAPPER_CONTENT)

      self.assertEqual(self.grid.processComputerPartitionList(), slapgrid.SLAPGRID_SUCCESS)

      self.assertEqual(
        self.fexecute_call_list,
        [
          query_chain,
          ['firewall_cmd', '--direct', '--permanent', '--remove-rules', 'ipv4', 'filter', '0-whitelist'],
          ['firewall_cmd', '--direct', '--permanent', '--remove-chain', 'ipv4', 'filter', '0-whitelist'],
          query_owner_rule,
          ['firewall_cmd', '--direct', '--permanent', '--remove-rule', 'ipv4', 'filter', 'OUTPUT', '0', '-m', 'owner', '--uid-owner', self.uid_owner, '-j', '0-whitelist'],
          ['firewall_cmd', '--reload']
        ]
      )
      self.assertFalse(os.path.exists(self.whitelist_firewall_md5sum))

  def test_damaged(self):
    with self._mock_requests():
      with open(self.whitelist_firewall_filename, 'w+') as f:
        f.write('nothing')

      self.partition.requested_state = 'started'
      self.partition.software.setBuildout(WRAPPER_CONTENT)

      self.assertEqual(self.grid.processComputerPartitionList(), slapgrid.SLAPGRID_SUCCESS)

      self.assertEqual(self.fexecute_call_list, [])
      self.assertFalse(os.path.exists(self.whitelist_firewall_md5sum))

  def test_not_list(self):
    with self._mock_requests():
      with open(self.whitelist_firewall_filename, 'w+') as f:
        json.dump({'127.0.0.1': '127.0.0.2'}, f)

      self.partition.requested_state = 'started'
      self.partition.software.setBuildout(WRAPPER_CONTENT)

      self.assertEqual(self.grid.processComputerPartitionList(), slapgrid.SLAPGRID_SUCCESS)

      self.assertEqual(self.fexecute_call_list, [])
      self.assertFalse(os.path.exists(self.whitelist_firewall_md5sum))

  def test_with_bad_entry(self):
    with self._mock_requests():
      with open(self.whitelist_firewall_filename, 'w+') as f:
        json.dump(['127.0.0.1', 'superpaczynka127.0.0.1', '::1'], f)

      self.partition.requested_state = 'started'
      self.partition.software.setBuildout(WRAPPER_CONTENT)

      self.assertEqual(self.grid.processComputerPartitionList(), slapgrid.SLAPGRID_SUCCESS)

      self.assertEqual(
        self.fexecute_call_list,
        [
          ['firewall_cmd', '--direct', '--permanent', '--query-chain', 'ipv4', 'filter', '0-whitelist'],
          ['firewall_cmd', '--direct', '--permanent', '--add-chain', 'ipv4', 'filter', '0-whitelist'],
          ['firewall_cmd', '--direct', '--permanent', '--remove-rules', 'ipv4', 'filter', '0-whitelist'],
          ['firewall_cmd', '--direct', '--permanent', '--add-rule', 'ipv4', 'filter', '0-whitelist', '0', '-d', u'127.0.0.1', '-j', 'ACCEPT'],
          ['firewall_cmd', '--direct', '--permanent', '--add-rule', 'ipv4', 'filter', '0-whitelist', '0', '-j', 'REJECT'],
          ['firewall_cmd', '--direct', '--permanent', '--query-rule', 'ipv4', 'filter', 'OUTPUT', '0', '-m', 'owner', '--uid-owner', self.uid_owner, '-j', '0-whitelist'],
          ['firewall_cmd', '--direct', '--permanent', '--add-rule', 'ipv4', 'filter', 'OUTPUT', '0', '-m', 'owner', '--uid-owner', self.uid_owner, '-j', '0-whitelist'],
          ['firewall_cmd', '--reload']]
      )
      with open(self.whitelist_firewall_filename, 'rb') as fh:
        expected_md5sum = hashlib.md5(fh.read().strip()).hexdigest()
      try:
        with open(self.whitelist_firewall_md5sum, 'rb') as fh:
          got_md5sum = fh.read().strip().decode('utf-8')
      except Exception:
        got_md5sum = None
      self.assertEqual(expected_md5sum, got_md5sum)

  def test_cleanup_on_destroy(self):
    with self._mock_requests():
      with open(self.whitelist_firewall_md5sum, 'w+') as fh:
        fh.write('')
      query_chain = ['firewall_cmd', '--direct', '--permanent', '--query-chain', 'ipv4', 'filter', '0-whitelist']
      query_owner_rule = ['firewall_cmd', '--direct', '--permanent', '--query-rule', 'ipv4', 'filter', 'OUTPUT', '0', '-m', 'owner', '--uid-owner', self.uid_owner, '-j', '0-whitelist']
      # setup side effects
      self.fexecute_side_effect[str(query_chain)] = (0, 'yes')
      self.fexecute_side_effect[str(query_owner_rule)] = (0, 'yes')
      self.partition.requested_state = 'destroyed'
      self.partition.software.setBuildout(WRAPPER_CONTENT)

      self.assertEqual(self.grid.agregateAndSendUsage(), slapgrid.SLAPGRID_SUCCESS)

      self.assertEqual(
        self.fexecute_call_list,
        [
          query_chain,
          ['firewall_cmd', '--direct', '--permanent', '--remove-rules', 'ipv4', 'filter', '0-whitelist'],
          ['firewall_cmd', '--direct', '--permanent', '--remove-chain', 'ipv4', 'filter', '0-whitelist'],
          query_owner_rule,
          ['firewall_cmd', '--direct', '--permanent', '--remove-rule', 'ipv4', 'filter', 'OUTPUT', '0', '-m', 'owner', '--uid-owner', self.uid_owner, '-j', '0-whitelist'],
          ['firewall_cmd', '--reload']
        ]
      )
      self.assertFalse(os.path.exists(self.whitelist_firewall_md5sum))
      # check cleanup no-op
      self.fexecute_call_list = []
      # setup side effects
      self.fexecute_side_effect[str(query_chain)] = (0, 'no')
      self.fexecute_side_effect[str(query_owner_rule)] = (0, 'no')
      self.partition.requested_state = 'destroyed'
      self.partition.software.setBuildout(WRAPPER_CONTENT)

      self.assertEqual(self.grid.agregateAndSendUsage(), slapgrid.SLAPGRID_SUCCESS)

      self.assertEqual(
        self.fexecute_call_list,
        [
          query_chain,
          query_owner_rule
        ]
      )


class TestSlapgridManagerLifecycle(MasterMixin, unittest.TestCase):

  def setUp(self):
    MasterMixin.setUp(self)

    self.manager = DummyManager()
    self.manager_list = [self.manager]
    self.setSlapgrid()

    self.computer = self.getTestComputerClass()(self.software_root, self.instance_root)

  def _mock_requests(self):
    return httmock.HTTMock(self.computer.request_handler)

  def test_partition_instance(self):
    with self._mock_requests():
      partition = self.computer.instance_list[0]

      partition.requested_state = 'started'
      partition.software.setBuildout(WRAPPER_CONTENT)
      self.assertEqual(self.grid.processComputerPartitionList(), slapgrid.SLAPGRID_SUCCESS)

      self.assertEqual(self.computer.sequence,
                       ['/getFullComputerInformation',
                        '/getComputerPartitionCertificate',
                        '/startedComputerPartition'])
      self.assertEqual(partition.state, 'started')

      self.assertEqual(self.manager.sequence,
                       ['instance', 'instanceTearDown'])

  def test_partition_software(self):
    with self._mock_requests():
      software = self.computer.software_list[0]

      buildout = """#!/bin/sh
echo "Kitty cute kitkat"
"""
      software.setBuildout(buildout)
      self.launchSlapgridSoftware()

      self.assertEqual(self.manager.sequence,
                       ['software', 'softwareTearDown'])

  def test_partition_software_fail(self):
    """Manager.softwareTearDown should not run when software release fail.
    """
    with self._mock_requests():
      software = self.computer.software_list[0]

      buildout = """#!/bin/sh
echo "Kitty cute kitkat"
exit 1
"""
      software.setBuildout(buildout)
      self.launchSlapgridSoftware()

      self.assertEqual(self.manager.sequence,
                       ['software'])

class TestBasicSlapgridPromise(BasicMixin, unittest.TestCase):
  def test_no_software_root(self):
    self.assertRaises(ConnectionError, self.grid.processPromiseList)

  def test_no_instance_root(self):
    os.mkdir(self.software_root)
    self.assertRaises(ConnectionError, self.grid.processPromiseList)

  def test_no_master(self):
    os.mkdir(self.software_root)
    os.mkdir(self.instance_root)
    self.assertRaises(ConnectionError, self.grid.processPromiseList)


class TestSlapgridPromiseWithMaster(MasterMixin, unittest.TestCase):

  fake_waiting_time = 0.05
  def test_one_failing_promise(self):
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    with httmock.HTTMock(computer.request_handler):
      instance = computer.instance_list[0]
      instance.requested_state = 'started'
      worked_file = os.path.join(instance.partition_path, 'fail_worked')
      fail = textwrap.dedent("""\
              #!/usr/bin/env sh
              touch "%s"
              exit 127""" % worked_file)
      instance.setPromise('fail', fail)
      self.assertEqual(self.grid.processPromiseList(),
                       slapos.grid.slapgrid.SLAPGRID_PROMISE_FAIL)
      self.assertTrue(os.path.isfile(worked_file))

  def test_one_failing_plugin_promise(self):
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    with httmock.HTTMock(computer.request_handler):
      instance = computer.instance_list[0]
      instance.requested_state = 'started'
      worked_file = os.path.join(instance.partition_path, 'fail_worked_plugin')
      fail = """import os
    with open("%s", 'a'):
      os.utime("%s", None)""" % (worked_file, worked_file)
      instance.setPluginPromise(promise_name='fail.py', success=False, promise_content=fail)
      self.assertEqual(self.grid.processPromiseList(),
                       slapos.grid.slapgrid.SLAPGRID_PROMISE_FAIL)
      self.assertTrue(os.path.isfile(worked_file))
      with open(os.path.join(instance.partition_path,
                ".slapgrid/promise/result/fail.status.json"), "r") as f:
        result = json.loads(f.read())
      self.assertEqual('failed', result["result"]["message"])

  def test_one_succeeding_promise(self):
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    with httmock.HTTMock(computer.request_handler):
      instance = computer.instance_list[0]
      instance.requested_state = 'started'
      worked_file = os.path.join(instance.partition_path, 'succeed_worked')
      succeed = textwrap.dedent("""\
              #!/usr/bin/env sh
              touch "%s"
              exit 0""" % worked_file)
      instance.setPromise('succeed', succeed)
      self.assertEqual(self.grid.processPromiseList(), slapgrid.SLAPGRID_SUCCESS)
      self.assertTrue(os.path.isfile(worked_file))

  def test_one_succeeding_plugin_promise(self):
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    with httmock.HTTMock(computer.request_handler):
      instance = computer.instance_list[0]
      instance.requested_state = 'started'
      worked_file = os.path.join(instance.partition_path, 'succeed_worked_plugin')
      succeed = """import os
    with open("%s", 'a'):
      os.utime("%s", None)""" % (worked_file, worked_file)
      instance.setPluginPromise(promise_name='succeeding.py',
                                success=True, promise_content=succeed)
      self.assertEqual(self.grid.processPromiseList(),
                       slapgrid.SLAPGRID_SUCCESS)
      self.assertTrue(os.path.isfile(worked_file))
      with open(os.path.join(instance.partition_path, ".slapgrid/promise/result/succeeding.status.json"), "r") as f:
        result = json.loads(f.read())

      self.assertEqual('success',
                       result["result"]["message"])

  def test_stderr_has_been_sent(self):
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    with httmock.HTTMock(computer.request_handler):
      instance = computer.instance_list[0]
      instance.requested_state = 'started'

      promise_path = os.path.join(instance.partition_path, 'etc', 'promise')
      os.makedirs(promise_path)
      succeed = os.path.join(promise_path, 'stderr_writer')
      worked_file = os.path.join(instance.partition_path, 'stderr_worked')
      with open(succeed, 'w') as f:
        f.write(textwrap.dedent("""\
              #!/usr/bin/env sh
              touch "%s"
              echo 'Error Promise 254554802' 1>&2
              exit 127""" % worked_file))
      os.chmod(succeed, 0o777)
      self.assertEqual(self.grid.processPromiseList(),
                       slapos.grid.slapgrid.SLAPGRID_PROMISE_FAIL)
      self.assertTrue(os.path.isfile(worked_file))

  def test_stderr_has_been_sent_plugin(self):
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    with httmock.HTTMock(computer.request_handler):
      instance = computer.instance_list[0]
      instance.requested_state = 'started'
      worked_file = os.path.join(instance.partition_path, 'stderr_worked_plugin')
      fail = """import os
    with open("%s", 'a'):
      os.utime("%s", None)
    raise ValueError("FAILED 254554802")""" % (worked_file, worked_file)
      instance.setPluginPromise(promise_name='stderr_fail.py', success=False, promise_content=fail)
      self.assertEqual(self.grid.processPromiseList(),
                       slapos.grid.slapgrid.SLAPGRID_PROMISE_FAIL)
      self.assertTrue(os.path.isfile(worked_file))
      with open(os.path.join(instance.partition_path, ".slapgrid/promise/result/stderr_fail.status.json"), "r") as f:
        result = json.loads(f.read())

      self.assertEqual('FAILED 254554802', result["result"]["message"])

  def test_timeout_works(self):
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    with httmock.HTTMock(computer.request_handler):
      instance = computer.instance_list[0]

      instance.requested_state = 'started'

      promise_path = os.path.join(instance.partition_path, 'etc', 'promise')
      os.makedirs(promise_path)
      succeed = os.path.join(promise_path, 'timed_out_promise')
      worked_file = os.path.join(instance.partition_path, 'timed_out_worked')
      with open(succeed, 'w') as f:
        f.write(textwrap.dedent("""\
              #!/usr/bin/env sh
              touch "%s"
              sleep 25
              exit 0""" % worked_file))
      os.chmod(succeed, 0o777)
      self.assertEqual(self.grid.processPromiseList(),
                       slapos.grid.slapgrid.SLAPGRID_PROMISE_FAIL)
      self.assertTrue(os.path.isfile(worked_file))

  def test_timeout_works_plugin(self):
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    with httmock.HTTMock(computer.request_handler):
      instance = computer.instance_list[0]
      instance.requested_state = 'started'
      worked_file = os.path.join(instance.partition_path, 'timed_out_worked_plugin')
      fail = """import os
    with open("%s", 'a'):
      os.utime("%s", None)
    import time
    time.sleep(27)""" % (worked_file, worked_file)
      instance.setPluginPromise(promise_name='timeout_fail.py', success=True, promise_content=fail)
      self.assertEqual(self.grid.processPromiseList(),
                       slapos.grid.slapgrid.SLAPGRID_PROMISE_FAIL)
      self.assertTrue(os.path.isfile(worked_file))
      with open(os.path.join(instance.partition_path, ".slapgrid/promise/result/timeout_fail.status.json"), "r") as f:
        result = json.loads(f.read())

      self.assertEqual('Error: Promise timed out after 20 seconds',
                       result["result"]["message"])

  def test_two_succeeding_promises(self):
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    with httmock.HTTMock(computer.request_handler):
      instance = computer.instance_list[0]
      instance.requested_state = 'started'

      for i in range(2):
        worked_file = os.path.join(instance.partition_path, 'succeed_%s_worked' % i)
        succeed = textwrap.dedent("""\
              #!/usr/bin/env sh
              touch "%s"
              exit 0""" % worked_file)
        instance.setPromise('succeed_%s' % i, succeed)

      self.assertEqual(self.grid.processPromiseList(), slapgrid.SLAPGRID_SUCCESS)
      for i in range(2):
        worked_file = os.path.join(instance.partition_path, 'succeed_%s_worked' % i)
        self.assertTrue(os.path.isfile(worked_file))

  def test_two_succeeding_plugin_promise(self):
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    with httmock.HTTMock(computer.request_handler):
      instance = computer.instance_list[0]
      instance.requested_state = 'started'
      worked_file = os.path.join(instance.partition_path, 'succeed_worked_plugin')
      succeed = """import os
    with open("%s", 'a'):
      os.utime("%s", None)""" % (worked_file, worked_file)
      instance.setPluginPromise(promise_name='succeeding.py',
                                success=True, promise_content=succeed)

      worked2_file = os.path.join(instance.partition_path, 'succeed_worked2_plugin')
      succeed = """import os
    with open("%s", 'a'):
      os.utime("%s", None)""" % (worked2_file, worked2_file)

      instance.setPluginPromise(promise_name='succeeding2.py',
                                success=True, promise_content=succeed)
      self.assertEqual(self.grid.processPromiseList(),
                       slapgrid.SLAPGRID_SUCCESS)
      self.assertTrue(os.path.isfile(worked_file))
      self.assertTrue(os.path.isfile(worked2_file))

      with open(os.path.join(instance.partition_path, ".slapgrid/promise/result/succeeding2.status.json"), "r") as f:
        result = json.loads(f.read())

      self.assertEqual('success',
                       result["result"]["message"])

      with open(os.path.join(instance.partition_path, ".slapgrid/promise/result/succeeding.status.json"), "r") as f:
        result = json.loads(f.read())

      self.assertEqual('success',
                       result["result"]["message"])


  def test_one_succeeding_one_failing_promises(self):
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    with httmock.HTTMock(computer.request_handler):
      instance = computer.instance_list[0]
      instance.requested_state = 'started'

      for i in range(2):
        worked_file = os.path.join(instance.partition_path, 'promise_worked_%d' % i)
        lockfile = os.path.join(instance.partition_path, 'lock')
        promise = textwrap.dedent("""\
                  #!/usr/bin/env sh
                  touch "%(worked_file)s"
                  if [ ! -f %(lockfile)s ]
                  then
                    touch "%(lockfile)s"
                    exit 0
                  else
                    exit 127
                  fi""" % {
            'worked_file': worked_file,
            'lockfile': lockfile
        })
        instance.setPromise('promise_%s' % i, promise)
      self.assertEqual(self.grid.processPromiseList(),
                       slapos.grid.slapgrid.SLAPGRID_PROMISE_FAIL)

  def test_one_succeeding_one_failing_promises_plugin(self):
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    with httmock.HTTMock(computer.request_handler):
      instance = computer.instance_list[0]
      instance.requested_state = 'started'
      worked_file = os.path.join(instance.partition_path, 'succeed_worked_plugin')
      succeed = """import os
    with open("%s", 'a'):
      os.utime("%s", None)""" % (worked_file, worked_file)
      instance.setPluginPromise(promise_name='succeeding.py',
                                success=True, promise_content=succeed)

      fail_file = os.path.join(instance.partition_path, 'fail_worked_plugin')
      fail = """import os
    with open("%s", 'a'):
      os.utime("%s", None)""" % (fail_file, fail_file)
      instance.setPluginPromise(promise_name='fail.py', success=False, promise_content=fail)

      self.assertEqual(self.grid.processPromiseList(),
                       slapgrid.SLAPGRID_PROMISE_FAIL)
      self.assertTrue(os.path.isfile(worked_file))
      self.assertTrue(os.path.isfile(fail_file))

      with open(os.path.join(instance.partition_path,
                ".slapgrid/promise/result/fail.status.json"), "r") as f:
        result = json.loads(f.read())
      self.assertEqual('failed', result["result"]["message"])

      with open(os.path.join(instance.partition_path, ".slapgrid/promise/result/succeeding.status.json"), "r") as f:
        result = json.loads(f.read())

      self.assertEqual('success', result["result"]["message"])

  def test_one_succeeding_one_timing_out_promises(self):
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    with httmock.HTTMock(computer.request_handler):
      instance = computer.instance_list[0]
      instance.requested_state = 'started'
      for i in range(2):
        worked_file = os.path.join(instance.partition_path, 'promise_worked_%d' % i)
        lockfile = os.path.join(instance.partition_path, 'lock')
        promise = textwrap.dedent("""\
                  #!/usr/bin/env sh
                  touch "%(worked_file)s"
                  if [ ! -f %(lockfile)s ]
                  then
                    touch "%(lockfile)s"
                  else
                    sleep 25
                  fi
                  exit 0""" % {
            'worked_file': worked_file,
            'lockfile': lockfile}
        )
        instance.setPromise('promise_%d' % i, promise)

      self.assertEqual(self.grid.processPromiseList(),
                       slapos.grid.slapgrid.SLAPGRID_PROMISE_FAIL)

  def test_one_succeeding_one_failing_promises_plugin(self):
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    with httmock.HTTMock(computer.request_handler):
      instance = computer.instance_list[0]
      instance.requested_state = 'started'
      worked_file = os.path.join(instance.partition_path, 'succeed_worked_plugin')
      succeed = """import os
    with open("%s", 'a'):
      os.utime("%s", None)""" % (worked_file, worked_file)
      instance.setPluginPromise(promise_name='succeeding.py',
                                success=True, promise_content=succeed)

      timeout_file = os.path.join(instance.partition_path, 'timed_out_worked_plugin')
      fail = """import os
    with open("%s", 'a'):
      os.utime("%s", None)
    import time
    time.sleep(27)""" % (timeout_file, timeout_file)
      instance.setPluginPromise(promise_name='timeout_fail.py', success=True, promise_content=fail)

      self.assertEqual(self.grid.processPromiseList(),
                       slapgrid.SLAPGRID_PROMISE_FAIL)
      self.assertTrue(os.path.isfile(worked_file))
      self.assertTrue(os.path.isfile(timeout_file))
      with open(os.path.join(instance.partition_path, ".slapgrid/promise/result/succeeding.status.json"), "r") as f:
        result = json.loads(f.read())

      self.assertEqual('success', result["result"]["message"])

      with open(os.path.join(instance.partition_path, ".slapgrid/promise/result/timeout_fail.status.json"), "r") as f:
        result = json.loads(f.read())

      self.assertEqual('Error: Promise timed out after 20 seconds',
                       result["result"]["message"])

  def test_promise_notrun_if_partition_stopped(self):
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    with httmock.HTTMock(computer.request_handler):
      instance = computer.instance_list[0]
      instance.requested_state = 'stopped'
      promise_file = os.path.join(instance.partition_path, 'promise_ran')
      promise = textwrap.dedent("""\
              #!/usr/bin/env sh
              touch "%s"
              exit 127""" % promise_file)
      instance.setPromise('promise_script', promise)
      self.assertEqual(self.grid.processPromiseList(),
                       slapos.grid.slapgrid.SLAPGRID_SUCCESS)
      self.assertFalse(os.path.exists(promise_file))

  def test_promise_notrun_if_partition_stopped_plugin(self):
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    with httmock.HTTMock(computer.request_handler):
      instance = computer.instance_list[0]
      instance.requested_state = 'stopped'
      worked_file = os.path.join(instance.partition_path, 'fail_worked_plugin')
      fail = """import os
    with open("%s", 'a'):
      os.utime("%s", None)""" % (worked_file, worked_file)
      instance.setPluginPromise(promise_name='fail.py', success=False, promise_content=fail)
      self.assertEqual(self.grid.processPromiseList(),
                       slapos.grid.slapgrid.SLAPGRID_SUCCESS)
      self.assertFalse(os.path.isfile(worked_file))
      self.assertFalse(os.path.isfile(os.path.join(instance.partition_path,
                ".slapgrid/promise/result/fail.status.json")))


class TestSlapgridPluginPromiseWithInstancePython(TestSlapgridPromiseWithMaster):
  expect_plugin = False

  def setMock(self):
    # unlike BasicMixin.setMock, we don't want to patch
    # slapos.grid.SlapObject.getPythonExecutableFromSoftwarePath
    pass

  def setPython(self):
    self.python_called = os.path.join(self.software_root, 'called')
    wrapper = """#!/bin/sh
    touch %s
    exec %s "$@"
    """ % (self.python_called, sys.executable)
    path = os.path.join(self.software_root, 'python')
    with open(path, 'w') as f:
      f.write(wrapper)
    os.chmod(path, 0o755)
    return path

  def getTestComputerClass(self):
    # use a test computer class modified to use a different python, that
    # will leave a `self.python_called` file when it's called so that we
    # can assert that our custom python was executed, and not the slapos.core
    # running python.

    test_self = self
    class TestComputerWithBuildout(
        super(TestSlapgridPluginPromiseWithInstancePython,
              self).getTestComputerClass()):

      def getTestSoftwareClass(self):
        class SoftwareForTestWithBuildout(
            super(TestComputerWithBuildout, self).getTestSoftwareClass()):
          def setBuildout(self, buildout=None):
            buildout = '#!' + test_self.setPython()
            return super(SoftwareForTestWithBuildout,
                         self).setBuildout(buildout)
        return SoftwareForTestWithBuildout

      def getTestInstanceClass(self):
        class InstanceForTestWithBuildout(
            super(TestComputerWithBuildout, self).getTestInstanceClass()):
          def setPluginPromise(self, *args, **kwargs):
            test_self.expect_plugin = self.requested_state == 'started'
            return super(InstanceForTestWithBuildout,
                         self).setPluginPromise(*args, **kwargs)
        return InstanceForTestWithBuildout

    return TestComputerWithBuildout

  def tearDown(self):
    try:
      os.remove(self.python_called)
      called = True
    except OSError as e:
      if e.errno != errno.ENOENT:
        raise
      called = False
    finally:
      super(TestSlapgridPluginPromiseWithInstancePython, self).tearDown()
    self.assertEqual(self.expect_plugin, called)

  def test_failed_promise_output(self):
    computer = self.getTestComputerClass()(self.software_root, self.instance_root, 1, 1)
    instance, = computer.instance_list

    instance.requested_state = 'started'
    instance.setPluginPromise(
        "failing_promise_plugin.py",
        promise_content="""if 1:
          return self.logger.error("héhé fake promise plugin error")
        """,
    )

    with httmock.HTTMock(computer.request_handler), \
        patch.object(self.grid.logger, 'info',) as dummyLogger:
      self.launchSlapgrid()

    self.assertEqual(
        dummyLogger.mock_calls[-1][1][0] % dummyLogger.mock_calls[-1][1][1:],
        "  0[(not ready)]: Promise 'failing_promise_plugin.py' failed with output: héhé fake promise plugin error")

  def test_succeeding_promise_logs_output(self):
    computer = self.getTestComputerClass()(self.software_root, self.instance_root, 1, 1)
    instance, = computer.instance_list

    name = "succeeding_promise_plugin.py"
    output = "hehe fake promise plugin succeded !"

    instance.requested_state = 'started'
    instance.setPluginPromise(
        name,
        promise_content="""if 1:
          return self.logger.info(%r)
        """ % output,
    )

    with httmock.HTTMock(computer.request_handler), \
        patch.object(self.grid.logger, 'info',) as dummyLogger:
      self.launchSlapgrid()

    self.assertIn(
      "Checking promise %s..." % name,
      dummyLogger.mock_calls[-4][1][0] % dummyLogger.mock_calls[-4][1][1:])

    self.assertIn(
      output,
      dummyLogger.mock_calls[-3][1][0] % dummyLogger.mock_calls[-3][1][1:])


class TestSlapgridPluginPromiseWithInstancePythonOldSlapOSCompatibility(
    TestSlapgridPluginPromiseWithInstancePython):
  """Process instance plugins with a different python, but simulate the case
  where plugin scripts structure had one extra import
  """

  def getTestComputerClass(self):
    # use a test computer that will use a custom python (because we reuse
    # TestSlapgridPluginPromiseWithInstancePython) and some promise plugins
    # scripts that look like the one slapos.cookbook was creating before 1.0.118
    class TestComputer(
        super(TestSlapgridPluginPromiseWithInstancePythonOldSlapOSCompatibility,
              self).getTestComputerClass()):
      def getTestInstanceClass(self):
        class TestInstance(super(TestComputer, self).getTestInstanceClass()):
          def setPluginPromise(self, *args, **kwargs):
            plugin_promise = super(TestInstance,
                                   self).setPluginPromise(*args, **kwargs)
            with open(plugin_promise) as f:
              plugin_code = f.read()

            legacy_plugin_code = plugin_code.replace(
                textwrap.dedent('''\
                      # coding: utf-8
                      import sys
                      '''),
                textwrap.dedent('''\
                      # coding: utf-8
                      import json
                      import sys
                      '''))
            assert legacy_plugin_code != plugin_code  # make sure our replace matched
            with open(plugin_promise, 'w') as f:
              f.write(legacy_plugin_code)
            return plugin_promise
        return TestInstance
    return TestComputer


class TestSVCBackend(unittest.TestCase):
  """Tests for supervisor backend.
  """
  def test_launchSupervisord_fail(self):
    """Proper message is displayed when supervisor can not be started.
    """
    logger = mock.create_autospec(logging.Logger)

    with self.assertRaisesRegex(
        RuntimeError,
        """Failed to launch supervisord:
Error: could not find config file /not/exist/etc/supervisord.conf
For help, use -c -h"""):
      slapos.grid.svcbackend.launchSupervisord('/not/exist', logger)

    logger.warning.assert_called()

  def _stop_process(self, process):
    # type: (subprocess.Process) -> None
    if process.poll() is None:
      process.terminate()
      process.wait()

  def test_supervisor_socket_legacy_path(self):
    """Check that supervisor uses legacy socket path if available.

    We changed the path of supervisor socket from supervisord.socket to sv.sock
    but we don't want createSupervisordConfiguration or launchSupervisord to use
    the new path if a supervisor is still running at the previous path.
    """
    instance_root = tempfile.mkdtemp()
    self.addCleanup(shutil.rmtree, instance_root)
    logger = mock.create_autospec(logging.Logger)

    slapos.grid.svcbackend.createSupervisordConfiguration(instance_root, logger)
    supervisord_config_file_path = os.path.join(instance_root, 'etc', 'supervisord.conf')
    with open(supervisord_config_file_path) as f:
      supervisord_config_file_content = f.read()
    self.assertIn('/sv.sock', supervisord_config_file_content)
    # change this config to use old socket
    with open(supervisord_config_file_path, 'w') as f:
      f.write(supervisord_config_file_content.replace('/sv.sock', '/supervisord.socket'))
    # start a supervisor on the old socket - this create the state of a running slapos
    # in the state before, when supervisord.socket was used as a socket name.
    supervisord_process = subprocess.Popen(
        ['supervisord', '--nodaemon', '-c', supervisord_config_file_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    self.addCleanup(self._stop_process, supervisord_process)

    # wait for process to be started
    supervisord_legacy_socket_path = os.path.join(instance_root, 'supervisord.socket')
    for i in range(20):
      if os.path.exists(supervisord_legacy_socket_path):
        break
      time.sleep(.1 * i)
    if supervisord_process.poll() is not None:
      self.fail(supervisord_process.communicate())

    # if we create config again, the legacy path will be used and config will not be overwritten
    slapos.grid.svcbackend.createSupervisordConfiguration(instance_root, logger)
    with open(supervisord_config_file_path) as f:
      supervisord_config_file_content = f.read()
    self.assertIn('/supervisord.socket', supervisord_config_file_content)
    self.assertNotIn('/sv.sock', supervisord_config_file_content)
    logger.info.assert_called_with('Using legacy supervisor socket path %s', supervisord_legacy_socket_path)

    slapos.grid.svcbackend.launchSupervisord(instance_root, logger)
    logger.debug.assert_called_with('Supervisord already running.')

  def test_stop_second_supervisord_after_supervisor_socket_path_change(self):
    """Check that supervisor uses legacy socket path if available.

    We changed the path of supervisor socket from supervisord.socket to sv.sock
    but we don't want createSupervisordConfiguration or launchSupervisord to use
    the new path if a supervisor is still running at the previous path.
    """
    instance_root = tempfile.mkdtemp()
    self.addCleanup(shutil.rmtree, instance_root)
    logger = mock.create_autospec(logging.Logger)

    slapos.grid.svcbackend.createSupervisordConfiguration(instance_root, logger)
    supervisord_config_file_path = os.path.join(instance_root, 'etc', 'supervisord.conf')
    with open(supervisord_config_file_path) as f:
      supervisord_config_file_content = f.read()
    self.assertIn('/sv.sock', supervisord_config_file_content)
    # change this config to use old socket
    with open(supervisord_config_file_path, 'w') as f:
      f.write(supervisord_config_file_content.replace('/sv.sock', '/supervisord.socket'))

    # start a first supervisor on the old socket
    supervisord_process_old_socket = subprocess.Popen(
        ['supervisord', '--nodaemon', '-c', supervisord_config_file_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    self.addCleanup(self._stop_process, supervisord_process_old_socket)

    # wait for process to be started
    supervisord_legacy_socket_path = os.path.join(instance_root, 'supervisord.socket')
    for i in range(20):
      if os.path.exists(supervisord_legacy_socket_path):
        break
      time.sleep(.1 * i)
    if supervisord_process_old_socket.poll() is not None:
      self.fail(supervisord_process_old_socket.communicate())

    # change this config to use new socket, as what happens when using slapos node 1.6.1
    with open(supervisord_config_file_path, 'w') as f:
      f.write(supervisord_config_file_content.replace('/supervisord.socket', '/sv.sock'))
    # start a second supervisor on the old socket
    supervisord_process_new_socket = subprocess.Popen(
        ['supervisord', '--nodaemon', '-c', supervisord_config_file_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    self.addCleanup(self._stop_process, supervisord_process_new_socket)

    # wait for process to be started
    supervisord_new_socket_path = os.path.join(instance_root, 'sv.sock')
    for i in range(20):
      if os.path.exists(supervisord_new_socket_path):
        break
      time.sleep(.1 * i)
    if supervisord_process_new_socket.poll() is not None:
      self.fail(supervisord_process_new_socket.communicate())

    # Now we have two supervisord processes running, like in the bad state created
    # by slapos.core 1.6.1

    # calling createSupervisordConfiguration should stop the supervisord listening
    # on the new socket
    slapos.grid.svcbackend.createSupervisordConfiguration(instance_root, logger)
    with open(supervisord_config_file_path) as f:
      supervisord_config_file_content = f.read()
    self.assertIn('/supervisord.socket', supervisord_config_file_content)
    self.assertNotIn('/sv.sock', supervisord_config_file_content)

    # process on new (sv.sock) will now exit
    for i in range(20):
      if supervisord_process_new_socket.poll() is not None:
        break
      time.sleep(.1 * i)
    self.assertEqual(
        supervisord_process_new_socket.poll(),
        0,
        supervisord_process_new_socket.communicate())
    self.assertFalse(os.path.exists(supervisord_new_socket_path))
    # process on old socket is still runnning
    if supervisord_process_old_socket.poll() is not None:
      self.fail(supervisord_process_old_socket.communicate())

    logger.critical.assert_called_with(
        'We have two supervisord running ! Stopping the one using %s to keep using legacy %s instead',
        supervisord_new_socket_path,
        supervisord_legacy_socket_path,
    )


class TestSlapgridPartitionTimeoutWithMaster(MasterMixin, unittest.TestCase):
  def _test(self, partition_timeout, delay, result):
    computer = self.getTestComputerClass()(self.software_root, self.instance_root)
    with httmock.HTTMock(computer.request_handler):
      instance = computer.instance_list[0]
      instance.requested_state = 'started'
      instance.software.setBuildout('#!/bin/sh\nsleep %s' % (delay,))
      self.setSlapgrid(develop=False, force_stop=False)
      self.grid.partition_timeout = partition_timeout
      self.assertEqual(result, self.grid.processComputerPartitionList())

  def test_timeouted(self):
    self._test(1, 2, 1)

  def test_finished(self):
    self._test(2, 1, 0)

  def test_default(self):
    self._test(None, 2, 0)
