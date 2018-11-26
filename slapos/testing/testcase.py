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

from .utils import findFreeTCPPort

from ..slap.standalone import StandaloneSlapOS
from ..slap.standalone import SlapOSNodeCommandError


# XXX -> utils
def _getPortFromPath(path):
  """A stable port using a hash from path.
  """
  import hashlib
  return (int(hashlib.md5(path).hexdigest(), 16) + 1024) \
        % (65535 - 1024)


# TODO:
#  - split slapos logic in methods ( supply, request etc )
#  - stop processes at the end
#  - build software in setup module
#  - allow requesting multiple instances ? no -> make another class

class SlapOSInstanceTestCase(unittest.TestCase):
  """Install one slapos instance.

  This test case install software(s) and request one instance during `setUpClass`
  and destroy the instance during `tearDownClass`.

  Software Release URL, Instance Software Type and Instance Parameters can be defined
  on the class.

  All tests from the test class will run with the same instance.

  The following class attributes are available:

    * `computer_partition`:  the `slapos.core.XXX` computer partition instance.

    * `computer_partition_root_path`: the path of the instance root directory,

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
  # Methods to be defined by subclasses.
  @classmethod
  def getSoftwareURLList(cls):
    """Return URL of software releases to install.

    To be defined by subclasses.
    """
    raise NotImplementedError()

  @classmethod
  def getInstanceParameterDict(cls):
    """Return instance parameters

    To be defined by subclasses if they need to request instance with specific
    parameters.
    """
    return {}

  @classmethod
  def getInstanceSoftwareType(cls):
    """Return software type for instance, default "default"

    To be defined by subclasses if they need to request instance with specific
    software type.
    """
    return "default"

  # Utility methods.
  def getSupervisorRPCServer(self):
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
    """Setup the class, build software and request an instance.

    If you have to override this method, do not forget to call this method on
    parent class.
    """
    try:
      # init
      ipv4_address = os.environ.get('LOCAL_IPV4', '127.0.1.1')
      ipv6_address = os.environ['GLOBAL_IPV6']
      base_directory = '/tmp/slaps/' # XXX

      cls.slap = StandaloneSlapOS(
          base_directory=base_directory, # XXX
          server_ip=ipv4_address,
          server_port=_getPortFromPath(base_directory)
      )
      # format
      cls.slap.format(
          partition_count=10,
          ipv4_address=ipv4_address,
          ipv6_address=ipv6_address,
      )
      # supply
      for software_url in cls.getSoftwareURLList():
        cls.slap.supply(software_url)

      # node software
      try:
        cls.slap.waitForSoftware(max_retry=3)
      except SlapOSNodeCommandError as e:
        raise cls.failureException(
            "Building softwares failed\n{}".format(e.args[0]['output']))


      # XXX this loop is silly, we in fact support only one the first software.
      def request():
        computer_partition_list = []
        for i, software_url in enumerate(cls.getSoftwareURLList()):
          computer_partition_list.append(
            cls.slap.request(
              software_release=software_url,
              software_type=cls.getInstanceSoftwareType(),
              partition_reference='testing partition {i}'.format(**locals()),
              partition_parameter_kw=cls.getInstanceParameterDict()))
        return computer_partition_list

      # request
      request()

      # node instance
      try:
        cls.slap.waitForInstance(max_retry=1)
      except SlapOSNodeCommandError as e:
        if e.args[0]['exitstatus'] != 2:
          # XXX we ignore promise error
          raise cls.failureException(
              "Requesting instances failed\n{}".format(e.args[0]['output']))

      # request
      computer_partition_list = request()

      # expose attributes

      # expose some class attributes so that tests can use them:
      # the ComputerPartition instances, to getInstanceParameterDict
      cls.computer_partition = computer_partition_list[0]

      # the path of the instance on the filesystem, for low level inspection
      cls.computer_partition_root_path = os.path.join(
          cls.slap._instance_root,
          cls.computer_partition.getId())

    except BaseException:
      cls.slap.shutdown()
      cls.setUp = lambda self: self.fail('Setup Class failed.')
      raise

  @classmethod
  def tearDownClass(cls):
    """Tear down class, stop the processes and destroy instance.
    """
    cls.slap.shutdown()
