# -*- coding: utf-8 -*-
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
import logging
import StringIO
from six.moves import xmlrpc_client as xmlrpclib

import supervisor.xmlrpc

try:
  import subprocess32 as subprocess
except ImportError:
  import subprocess

from .utils import findFreeTCPPort
from .utils import getPortFromPath

from ..slap.standalone import StandaloneSlapOS
from ..slap.standalone import SlapOSNodeCommandError
from ..slap.standalone import PathTooDeepError


# XXX SLAPOS_* environment variables should not be used here.
class TestingSlapOSInstance(object):
  """A singleton StandaloneSlapOS instance, using ip addresses defined by
  environment variables SLAPOS_TEST_IPV4 and SLAPOS_TEST_IPV6.

  The working directory is .slapos in current directory, or a path from
  SLAPOS_TEST_WORKING_DIR environment variable.

  A note about paths:
    SlapOS itself and some services running in SlapOS uses unix sockets and (sometimes very)
    deep path, which does not play very well together. To workaround this, users can
    set SLAPOS_TEST_WORKING_DIR enivonment variable to the path of a short enough directory
    and local slapos will be in this directory.
    The partitions references will be named after the unittest class name, which can also lead
    to long paths. For this, unit test classes can define a __partition_reference__ attribute
    which will be used as partition reference. The trick is then to use a shorter
    __partition_reference__
  See https://lab.nexedi.com/kirr/slapns for the solution to all these problems.
  """
  def __new__(cls):
    if not hasattr(cls, 'slap') or not cls.slap:
      ipv4_address = os.environ['SLAPOS_TEST_IPV4']
      ipv6_address = os.environ['SLAPOS_TEST_IPV6']
      base_directory = os.environ.get(
          'SLAPOS_TEST_WORKING_DIR',
          os.path.join(os.getcwd(), '.slapos'))
      if not os.path.exists(base_directory):
        os.mkdir(base_directory)
      try:
        cls.slap = StandaloneSlapOS(
            base_directory=base_directory,
            server_ip=ipv4_address,
            server_port=getPortFromPath(base_directory)
        )
      except PathTooDeepError as e:
        raise RuntimeError('base directory ( {} ) is too deep, try setting '
              'SLAPOS_TEST_WORKING_DIR to a shallow enough directory'.format(base_directory))

      cls.slap.format(
          partition_count=10,
          ipv4_address=ipv4_address,
          ipv6_address=ipv6_address,
      )
    return cls.slap


def installSoftwareUrlList(software_url_list, max_retry=2, debug=False):
  """Install some softwares on the current testing slapos, to be used in `setUpModule`
  """
  slapos = TestingSlapOSInstance()
  for software_url in software_url_list:
    slapos.supply(software_url)
  slapos.waitForSoftware(max_retry=max_retry, debug=debug)



class SlapOSTestCase(unittest.TestCase):
  """Simple class with access to slapos
  """
  @classmethod
  def setUpClass(cls):
    """Starts the SlapOS
    """
    cls.slap = TestingSlapOSInstance()
    cls.slap.start()

  @classmethod
  def tearDownClass(cls):
    """Tear down class, stop the processes
    """
    cls.slap.stop()


class SlapOSInstanceTestCase(SlapOSTestCase):
  """Install one slapos instance.

  This test case install software(s) and request one instance during `setUpClass`
  and destroy the instance during `tearDownClass`.

  Software Release URL, Instance Software Type and Instance Parameters can be defined
  on the class.

  All tests from the test class will run with the same instance.

  The following class attributes are available:

    * `computer_partition`:  the `slapos.slap.slap.ComputerPartition` computer partition instance.

    * `computer_partition_root_path`: the path of the instance root directory,

  """
  # can set this to true to enable debugging utilities
  debug = False
  # maximum retries for `slapos node instance`
  instance_max_retry = 0
  # ignore promises failure during `slapos node instance`
  ignore_promise_during_instanciation = False
  # maximum retries for `slapos node report`
  report_max_retry = 0

  # Methods to be defined by subclasses.
  @classmethod
  def getSoftwareURL(cls):
    """Return URL of software release to request instance.

    To be defined by subclasses.
    Note that software has to be installed on the slapos, using installSoftwareUrlList, preferably in setUpModule
    """
    raise NotImplementedError()

  @classmethod
  def getInstanceParameterDict(cls):
    """Return instance parameters.

    To be defined by subclasses if they need to request instance with specific
    parameters.
    """
    return {}

  @classmethod
  def getInstanceSoftwareType(cls):
    """Return software type for instance, default "default".

    To be defined by subclasses if they need to request instance with specific
    software type.
    """
    return "default"

  # Utility methods.
  def getSupervisorRPC(self):
    """Returns a XML-RPC connection to the supervisor used by slapos node

    Refer to http://supervisord.org/api.html for details of available methods.
    """
    # TODO: make it a context manager
    # xmlrpc over unix socket https://stackoverflow.com/a/11746051/7294664
    return xmlrpclib.ServerProxy(
       'http://slapos-supervisor',
       transport=supervisor.xmlrpc.SupervisorTransport(
           None,
           None,
           # XXX hardcoded socket path
           serverurl="unix://{self.slap._instance_root}/supervisord.socket".format(
               **locals())))

  # Unittest methods
  @classmethod
  def setUpClass(cls):
    """Request an instance.
    """
    super(SlapOSInstanceTestCase, cls).setUpClass()
    try:
      # request
      cls.__request()

      # slapos node instance
      try:
        cls.slap.waitForInstance(max_retry=cls.instance_max_retry, debug=cls.debug)
      except SlapOSNodeCommandError as e:
        # exitstatus 2 means promise failed
        # XXX check this .args[0] is OK with python 2 & 3
        if not (cls.ignore_promise_during_instanciation and e.args[0]['exitstatus'] == 2):
          # XXX we ignore promise error
          raise cls.failureException(
              "Requesting instance failed\n{}".format(e.args[0]['output']))
      except subprocess.CalledProcessError as e: # in debug mode command is executed directly
        if not (cls.ignore_promise_during_instanciation and e.returncode == 2):
          raise

      # expose some class attributes so that tests can use them:
      # the main ComputerPartition instance, to use getInstanceParameterDict
      cls.computer_partition = cls.__request()

      # the path of the instance on the filesystem, for low level inspection
      cls.computer_partition_root_path = os.path.join(
          cls.slap._instance_root,
          cls.computer_partition.getId())

    except BaseException:
      if hasattr(cls, 'slap'):
        cls.slap.stop()
      cls.setUp = lambda self: self.fail('Setup Class failed.')
      raise

  @classmethod
  def tearDownClass(cls):
    """Tear down class, stop the processes and destroy instance.
    """
    cls.__request(state='destroyed')
    cls.slap.waitForReport(max_retry=cls.report_max_retry, debug=cls.debug)
    super(SlapOSInstanceTestCase, cls).tearDownClass()

  # implementation methods
  @classmethod
  def __request(cls, state='started'):
    return cls.slap.request(
        software_release=cls.getSoftwareURL(),
        software_type=cls.getInstanceSoftwareType(),
        partition_reference='testing partition 0',
        partition_parameter_kw=cls.getInstanceParameterDict(),
        state=state)
