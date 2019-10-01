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
import glob
import logging

try:
  import subprocess32 as subprocess
except ImportError:
  import subprocess
  subprocess  # pyflakes

from .utils import getPortFromPath

from ..slap.standalone import StandaloneSlapOS
from ..slap.standalone import SlapOSNodeCommandError
from ..slap.standalone import PathTooDeepError
from ..grid.utils import md5digest

try:
  from typing import Iterable, Tuple, Callable, Type
except ImportError:
  pass


def makeModuleSetUpAndTestCaseClass(
    software_url,
    base_directory=None,
    ipv4_address=os.environ['SLAPOS_TEST_IPV4'],
    ipv6_address=os.environ['SLAPOS_TEST_IPV6'],
    debug=bool(int(os.environ.get('SLAPOS_TEST_DEBUG', 0))),
    verbose=bool(int(os.environ.get('SLAPOS_TEST_VERBOSE', 0))),
    shared_part_list=os.environ.get('SLAPOS_TEST_SHARED_PART_LIST',
                                    '').split(os.pathsep),
):
  # type: (str, str, str, str, bool, bool, List[str]) -> Tuple[Callable[[], None], Type[SlapOSInstanceTestCase]]
  """Create a setup module function and a testcase for testing `software_url`.

  This function returns a tuple of two arguments:
   * a function to install the software, to be used as `unittest`'s
     `setUpModule`
   * a base class for test cases.

  The SlapOS instance will be using ip addresses defined by
  environment variables `SLAPOS_TEST_IPV4` and `SLAPOS_TEST_IPV6`, or by the
  explicits `ipv4_address` and `ipv6_address` arguments.

  To ease development and troubleshooting, two switches are available:
   * `verbose` (also controlled by `SLAPOS_TEST_VERBOSE` environment variable)
     to tell the test framework to log information describing the actions taken.
   * `debug` (also controlled by `SLAPOS_TEST_DEBUG` environment variable) to
     enable debugging mode which will drop in a debugger session when errors
     occurs.

  The base_directory directory is by default .slapos in current directory,
  or a path from `SLAPOS_TEST_WORKING_DIR` environment variable.

  This test class will use its own directory for shared parts and can also
  paths from `shared_part_list` argument to lookup existing parts.
  This is controlled by SLAPOS_TEST_SHARED_PART_LIST environment variable,
  which should be a : separated list of path.

  A note about paths:
    SlapOS itself and some services running in SlapOS uses unix sockets and
    (sometimes very) deep paths, which does not play very well together.
    To workaround this, users can set `SLAPOS_TEST_WORKING_DIR` environment
    variable to the path of a short enough directory and local slapos will
    use this directory.
    The partitions references will be named after the unittest class name,
    which can also lead to long paths. For this, unit test classes can define
    a `__partition_reference__` attribute which will be used as partition
    reference. If the class names are long, the trick is then to use a shorter
    `__partition_reference__`.
    See https://lab.nexedi.com/kirr/slapns for a solution to this problem.
  """
  if base_directory is None:
    base_directory = os.path.realpath(
        os.environ.get(
            'SLAPOS_TEST_WORKING_DIR', os.path.join(os.getcwd(), '.slapos')))
  # TODO: fail if already running ?
  try:
    slap = StandaloneSlapOS(
        base_directory=base_directory,
        server_ip=ipv4_address,
        server_port=getPortFromPath(base_directory),
        shared_part_list=shared_part_list)
  except PathTooDeepError:
    raise RuntimeError(
        'base directory ( {} ) is too deep, try setting '
        'SLAPOS_TEST_WORKING_DIR to a shallow enough directory'.format(
            base_directory))

  cls = type(
      'SlapOSInstanceTestCase for {}'.format(software_url),
      (SlapOSInstanceTestCase,), {
          'slap': slap,
          'getSoftwareURL': classmethod(lambda _cls: software_url),
          '_debug': debug,
          '_verbose': verbose,
          '_ipv4_address': ipv4_address,
          '_ipv6_address': ipv6_address
      })

  class SlapOSInstanceTestCase_(cls, SlapOSInstanceTestCase):
    # useless intermediate class so that editors provide completion anyway.
    pass

  def setUpModule():
    # type: () -> None
    if debug:
      unittest.installHandler()
    if verbose or debug:
      logging.basicConfig(level=logging.DEBUG)
    installSoftwareUrlList(cls, [software_url], debug=debug)

  return setUpModule, SlapOSInstanceTestCase_


def checkSoftware(slap, software_url):
  # type: (StandaloneSlapOS, str) -> None
  """Check software installation.

  This perform a few basic static checks for common problems
  with software installations.
  """
  software_hash = md5digest(software_url)

  error_list = []
  # Check that all components set rpath correctly and we don't have miss linking any libraries.
  for path in (os.path.join(slap.software_directory,
                            software_hash), slap.shared_directory):
    if not glob.glob(os.path.join(path, '*')):
      # shared might be empty (when using a slapos command that does not support shared yet).
      continue
    out = ''
    try:
      out = subprocess.check_output(
          "find . -type f -executable "

          # We ignore parts that are binary distributions.
          "| egrep -v /parts/java-re.*/ "
          "| egrep -v /parts/firefox-.*/ "
          "| egrep -v /parts/chromium-.*/ "
          "| egrep -v /parts/chromedriver-.*/ "

          # nss has no valid rpath. It does not seem to be a problem in our case.
          "| egrep -v /parts/nss/ "
          "| xargs ldd "
          r"| egrep '(^\S|not found)' "
          "| grep -B1 'not found'",
          shell=True,
          stderr=subprocess.STDOUT,
          cwd=path,
      )
    except subprocess.CalledProcessError as e:
      # The "good case" is when grep does not match anything, but in
      # that case, it exists with exit code 1, so we accept this case.
      if e.returncode != 1 or e.output:
        error_list.append(e.output)
    if out:
      error_list.append(out)

  # check this software is not referenced in any shared parts.
  for signature_file in glob.glob(os.path.join(slap.shared_directory, '*', '*',
                                               '.*slapos.*.signature')):
    with open(signature_file) as f:
      signature_content = f.read()
      if software_hash in signature_content:
        error_list.append(
            "Software hash present in signature {}\n{}\n".format(
                signature_file, signature_content))

  if error_list:
    raise RuntimeError('\n'.join(error_list))


def installSoftwareUrlList(cls, software_url_list, max_retry=2, debug=False):
  # type: (Type[SlapOSInstanceTestCase], Iterable[str], int, bool) -> None
  """Install softwares on the current testing slapos, for use in `setUpModule`.

  This also check softwares with `checkSoftware`
  """
  try:
    for software_url in software_url_list:
      cls.logger.debug("Supplying %s", software_url)
      cls.slap.supply(software_url)
    cls.logger.debug("Waiting for slapos node software to build")
    cls.slap.waitForSoftware(max_retry=max_retry, debug=debug)
    for software_url in software_url_list:
      checkSoftware(cls.slap, software_url)
  except BaseException as e:
    if not debug:
      cls.logger.exception("Error building software, removing")
      try:
        for software_url in software_url_list:
          cls.logger.debug("Removing %s", software_url)
          cls.slap.supply(software_url, state="destroyed")
        cls.logger.debug("Waiting for slapos node software to remove")
        cls.slap.waitForSoftware(max_retry=max_retry, debug=debug)
      except BaseException:
        cls.logger.exception("Error removing software")
        pass
    cls._cleanup()
    raise e


class SlapOSInstanceTestCase(unittest.TestCase):
  """Install one slapos instance.

  This test case install software(s) and request one instance
  during `setUpClass` and destroy that instance during `tearDownClass`.

  Software Release URL, Instance Software Type and Instance Parameters
  can be defined on the class.

  All tests from the test class will run with the same instance.

  The following class attributes are available:

    * `computer_partition`:  the `slapos.slap.slap.ComputerPartition`
      computer partition instance.

    * `computer_partition_root_path`: the path of the instance root
      directory.

  This class is not supposed to be imported directly, but needs to be setup by
  calling makeModuleSetUpAndTestCaseClass.
  """
  # can set this to true to enable debugging utilities
  _debug = False
  # can set this to true to enable more verbose output
  _verbose = False
  # maximum retries for `slapos node instance`
  instance_max_retry = 10
  # maximum retries for `slapos node report`
  report_max_retry = 0
  # number of partitions needed for this instance
  partition_count = 10
  # reference of the default requested partition
  default_partition_reference = 'testing partition 0'

  # a logger for messages of the testing framework
  logger = logging.getLogger(__name__)

  # Dynamic members
  slap = None  # type: StandaloneSlapOS
  _ipv4_address = ""
  _ipv6_address = ""

  # Methods to be defined by subclasses.
  @classmethod
  def getSoftwareURL(cls):
    """Return URL of software release to request instance.

    This method will be defined when initialising the class
    with makeModuleSetUpAndTestCaseClass.
    """
    raise NotImplementedError()

  @classmethod
  def getInstanceParameterDict(cls):
    """Return instance parameters.

    To be defined by subclasses if they need to request instance
    with specific parameters.
    """
    return {}

  @classmethod
  def getInstanceSoftwareType(cls):
    """Return software type for instance, default "".

    To be defined by subclasses if they need to request instance with specific
    software type.
    """
    return ""

  # Unittest methods
  @classmethod
  def setUpClass(cls):
    """Request an instance.
    """
    cls._instance_parameter_dict = cls.getInstanceParameterDict()

    try:
      cls.logger.debug("Starting")
      cls.slap.start()
      cls.logger.debug(
          "Formatting to remove old partitions XXX should not be needed because we delete ..."
      )
      cls.slap.format(0, cls._ipv4_address, cls._ipv6_address)
      cls.logger.debug("Formatting with %s partitions", cls.partition_count)
      cls.slap.format(
          cls.partition_count, cls._ipv4_address, cls._ipv6_address,
          getattr(cls, '__partition_reference__', '{}-'.format(cls.__name__)))

      # request
      cls.requestDefaultInstance()

      # slapos node instance
      cls.logger.debug("Waiting for instance")
      # waitForInstance does not tolerate any error but with instances,
      # promises sometimes fail on first run, because services did not
      # have time to start.
      # To make debug usable, we tolerate instance_max_retry-1 errors and
      # only debug the last.
      if cls._debug and cls.instance_max_retry:
        try:
          cls.slap.waitForInstance(max_retry=cls.instance_max_retry - 1)
        except SlapOSNodeCommandError:
          cls.slap.waitForInstance(debug=True)
      else:
        cls.slap.waitForInstance(
            max_retry=cls.instance_max_retry, debug=cls._debug)

      # expose some class attributes so that tests can use them:
      # the main ComputerPartition instance, to use getInstanceParameterDict
      cls.computer_partition = cls.requestDefaultInstance()

      # the path of the instance on the filesystem, for low level inspection
      cls.computer_partition_root_path = os.path.join(
          cls.slap._instance_root, cls.computer_partition.getId())
      cls.logger.debug("setUpClass done")

    except BaseException:
      cls.logger.exception("Error during setUpClass")
      cls._cleanup()
      cls.setUp = lambda self: self.fail('Setup Class failed.')
      raise

  @classmethod
  def tearDownClass(cls):
    """Tear down class, stop the processes and destroy instance.
    """
    cls._cleanup()

  # implementation methods
  @classmethod
  def _cleanup(cls):
    """Destroy all instances and stop subsystem.
    Catches and log all exceptions.
    """
    try:
      cls.requestDefaultInstance(state='destroyed')
    except:
      cls.logger.exception("Error during request destruction")
    try:
      cls.slap.waitForReport(max_retry=cls.report_max_retry, debug=cls._debug)
    except:
      cls.logger.exception("Error during actual destruction")
    leaked_partitions = [
        cp for cp in cls.slap.computer.getComputerPartitionList()
        if cp.getState() != 'destroyed'
    ]
    if leaked_partitions:
      cls.logger.critical(
          "The following partitions were not cleaned up: %s",
          [cp.getId() for cp in leaked_partitions])
    for cp in leaked_partitions:
      try:
        cls.slap.request(
            software_release=cp.getSoftwareRelease().getURI(),
            # software_type=cp.getType(), # TODO
            # XXX is this really the reference ?
            partition_reference=cp.getInstanceParameterDict()['instance_title'],
            state="destroyed")
      except:
        cls.logger.exception(
            "Error during request destruction of leaked partition")
    try:
      cls.slap.waitForReport(max_retry=cls.report_max_retry, debug=cls._debug)
    except:
      cls.logger.exception("Error during leaked partitions actual destruction")
    try:
      cls.slap.stop()
    except:
      cls.logger.exception("Error during stop")

  @classmethod
  def requestDefaultInstance(cls, state='started'):
    software_url = cls.getSoftwareURL()
    software_type = cls.getInstanceSoftwareType()
    cls.logger.debug(
        'requesting "%s" software:%s type:%s state:%s parameters:%s',
        cls.default_partition_reference, software_url, software_type, state,
        cls._instance_parameter_dict)
    return cls.slap.request(
        software_release=software_url,
        software_type=software_type,
        partition_reference=cls.default_partition_reference,
        partition_parameter_kw=cls._instance_parameter_dict,
        state=state)
