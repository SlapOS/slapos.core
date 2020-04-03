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
import fnmatch
import re
import glob
import logging
import shutil
from six.moves.urllib.parse import urlparse

try:
  import subprocess32 as subprocess
except ImportError:
  import subprocess  # type: ignore
  subprocess  # pyflakes

from .utils import getPortFromPath

from ..slap.standalone import StandaloneSlapOS
from ..slap.standalone import SlapOSNodeCommandError
from ..slap.standalone import PathTooDeepError
from ..grid.utils import md5digest
from ..util import mkdir_p

try:
  from typing import Iterable, Tuple, Callable, Type, Dict, List, Optional
except ImportError:
  pass


def makeModuleSetUpAndTestCaseClass(
    software_url,
    base_directory=None,
    ipv4_address=os.environ['SLAPOS_TEST_IPV4'],
    ipv6_address=os.environ['SLAPOS_TEST_IPV6'],
    debug=bool(int(os.environ.get('SLAPOS_TEST_DEBUG', 0))),
    verbose=bool(int(os.environ.get('SLAPOS_TEST_VERBOSE', 0))),
    shared_part_list=[
        os.path.expanduser(p) for p in os.environ.get(
            'SLAPOS_TEST_SHARED_PART_LIST', '').split(os.pathsep)
    ],
    snapshot_directory=os.environ.get('SLAPOS_TEST_LOG_DIRECTORY'),
):
  # type: (str, str, str, str, bool, bool, Iterable[str], Optional[str]) -> Tuple[Callable[[], None], Type[SlapOSInstanceTestCase]]
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
  if not snapshot_directory:
    snapshot_directory = os.path.join(base_directory, "snapshots")

  cls = type(
      'SlapOSInstanceTestCase for {}'.format(software_url),
      (SlapOSInstanceTestCase,), {
          'slap': slap,
          'getSoftwareURL': classmethod(lambda _cls: software_url),
          'software_id': urlparse(software_url).path.split('/')[-2],
          '_debug': debug,
          '_verbose': verbose,
          '_ipv4_address': ipv4_address,
          '_ipv6_address': ipv6_address,
          '_base_directory': base_directory,
          '_test_file_snapshot_directory': snapshot_directory
      })

  class SlapOSInstanceTestCase_(
      cls,  # type: ignore # https://github.com/python/mypy/issues/2813
      SlapOSInstanceTestCase):
    # useless intermediate class so that editors provide completion anyway.
    pass

  def setUpModule():
    # type: () -> None
    if debug:
      unittest.installHandler()
    logging.basicConfig(
        level=logging.DEBUG if (verbose or debug) else logging.WARNING)
    installSoftwareUrlList(cls, [software_url], debug=debug)

  return setUpModule, SlapOSInstanceTestCase_


def checkSoftware(slap, software_url):
  # type: (StandaloneSlapOS, str) -> None
  """Check software installation.

  This perform a few basic static checks for common problems
  with software installations.
  """

  # Check that all components set rpath correctly and we don't have miss linking any libraries.
  # Also check that they are not linked against system libraries, except a white list of core
  # system libraries.
  system_lib_white_list = set((
      'libc',
      'libcrypt',
      'libdl',
      'libgcc_s',
      'libgomp',
      'libm',
      'libnsl',
      'libpthread',
      'libresolv',
      'librt',
      'libstdc++',
      'libutil',
  ))

  # we also ignore a few patterns for part that are known to be binary distributions,
  # for which we generate LD_LIBRARY_PATH wrappers or we don't use directly.
  ignored_file_patterns = set((
      '*/parts/java-re*/*',
      '*/parts/firefox*/*',
      '*/parts/chromium-*/*',
      '*/parts/chromedriver*/*',
      '*/parts/libreoffice-bin/*',
      '*/parts/wkhtmltopdf/*',
      # nss is not a binary distribution, but for some reason it has invalid rpath, but it does
      # not seem to be a problem in our use cases.
      '*/parts/nss/*',
      '*/node_modules/phantomjs*/*',
      '*/grafana/tools/phantomjs/*',
  ))

  software_hash = md5digest(software_url)
  error_list = []

  ldd_so_resolved_re = re.compile(
      r'\t(?P<library_name>.*) => (?P<library_path>.*) \(0x')
  ldd_already_loaded_re = re.compile(r'\t(?P<library_name>.*) \(0x')
  ldd_not_found_re = re.compile(r'.*not found.*')

  class DynamicLibraryNotFound(Exception):
    """Exception raised when ldd cannot resolve a library.
    """
  def getLddOutput(path):
    # type: (str) -> Dict[str, str]
    """Parse ldd output on shared object/executable as `path` and returns a mapping
    of library paths or None when library is not found, keyed by library so name.

    Raises a `DynamicLibraryNotFound` if any dynamic library is not found.

    Special entries, like VDSO ( linux-vdso.so.1 ) or ELF interpreter
    ( /lib64/ld-linux-x86-64.so.2 ) are ignored.
    """
    libraries = {}  # type: Dict[str, str]
    try:
      ldd_output = subprocess.check_output(
          ('ldd', path),
          stderr=subprocess.STDOUT,
          universal_newlines=True,
      )
    except subprocess.CalledProcessError as e:
      if e.output not in ('\tnot a dynamic executable\n',):
        raise
      return libraries
    if ldd_output == '\tstatically linked\n':
      return libraries

    not_found = []
    for line in ldd_output.splitlines():
      resolved_so_match = ldd_so_resolved_re.match(line)
      ldd_already_loaded_match = ldd_already_loaded_re.match(line)
      not_found_match = ldd_not_found_re.match(line)
      if resolved_so_match:
        libraries[resolved_so_match.group(
            'library_name')] = resolved_so_match.group('library_path')
      elif ldd_already_loaded_match:
        # VDSO or ELF, ignore . See https://stackoverflow.com/a/35805410/7294664 for more about this
        pass
      elif not_found_match:
        not_found.append(line)
      else:
        raise RuntimeError('Unknown ldd line %s for %s.' % (line, path))
    if not_found:
      not_found_text = '\n'.join(not_found)
      raise DynamicLibraryNotFound(
          '{path} has some not found libraries:\n{not_found_text}'.format(
              **locals()))
    return libraries

  def checkExecutableLink(paths_to_check, valid_paths_for_libs):
    # type: (Iterable[str], Iterable[str]) -> List[str]
    """Check shared libraries linked with executables in `paths_to_check`.
    Only libraries from `valid_paths_for_libs` are accepted.
    Returns a list of error messages.
    """
    executable_link_error_list = []
    for path in paths_to_check:
      for root, dirs, files in os.walk(path):
        for f in files:
          f = os.path.join(root, f)
          if any(fnmatch.fnmatch(f, ignored_pattern)
                 for ignored_pattern in ignored_file_patterns):
            continue
          if os.access(f, os.X_OK) or fnmatch.fnmatch('*.so', f):
            try:
              libs = getLddOutput(f)
            except DynamicLibraryNotFound as e:
              executable_link_error_list.append(str(e))
            else:
              for lib, lib_path in libs.items():
                if lib.split('.')[0] in system_lib_white_list:
                  continue
                lib_path = os.path.realpath(lib_path)
                # dynamically linked programs can only be linked with libraries
                # present in software or in shared parts repository.
                if any(lib_path.startswith(valid_path)
                       for valid_path in valid_paths_for_libs):
                  continue
                executable_link_error_list.append(
                    '{f} uses system library {lib_path} for {lib}'.format(
                        **locals()))
    return executable_link_error_list

  paths_to_check = (
      os.path.join(slap.software_directory, software_hash),
      slap.shared_directory,
  )
  error_list.extend(
      checkExecutableLink(
          paths_to_check,
          paths_to_check + tuple(slap._shared_part_list),
      ))

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
  def _storeSoftwareLogSnapshot(name):
    for standalone_log in glob.glob(os.path.join(
        cls._base_directory,
        'var',
        'log',
        '*',
    )):
      cls._copySnapshot(standalone_log, name)

  try:
    cls.logger.debug("Starting")
    cls.slap.start()
    for software_url in software_url_list:
      cls.logger.debug("Supplying %s", software_url)
      cls.slap.supply(software_url)
    cls.logger.debug("Waiting for slapos node software to build")
    cls.slap.waitForSoftware(max_retry=max_retry, debug=debug)
    _storeSoftwareLogSnapshot('setupModule')
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
        _storeSoftwareLogSnapshot('setupModule removing software')
    cls._cleanup('setupModule')
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
  report_max_retry = 10
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

  # a short name of that software URL.
  # eg. helloworld instead of
  # https://lab.nexedi.com/nexedi/slapos/raw/software/helloworld/software.cfg
  software_id = ""
  _base_directory = ""  # base directory for standalone
  _test_file_snapshot_directory = ""  # directory to save snapshot files for inspections
  # patterns of files to save for inspection, relative to instance directory
  _save_instance_file_pattern_list = (
      '*/bin/*',
      '*/etc/*',
      '*/var/log/*',
      '*/.*log',
      '*/.*cfg',
      '*/*cfg',
      'etc/',
  )

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
    snapshot_name = "{}.{}.setUpClass".format(cls.__module__, cls.__name__)

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
      cls._storeSystemSnapshot(snapshot_name)
      cls._cleanup(snapshot_name)
      cls.setUp = lambda self: self.fail('Setup Class failed.')
      raise
    else:
      cls._storeSystemSnapshot(snapshot_name)

  @classmethod
  def tearDownClass(cls):
    """Tear down class, stop the processes and destroy instance.
    """
    cls._cleanup("{}.{}.tearDownClass".format(cls.__module__, cls.__name__))
    if not cls._debug:
      cls.logger.debug(
          "cleaning up slapos log files in %s", cls.slap._log_directory)
      for log_file in glob.glob(os.path.join(cls.slap._log_directory, '*')):
        os.unlink(log_file)

  @classmethod
  def _storePartitionSnapshot(cls, name):
    """Store snapshot of partitions.

    This uses the definition from class attribute `_save_instance_file_pattern_list`
    """
    # copy config and log files from partitions
    for (dirpath, dirnames, filenames) in os.walk(cls.slap.instance_directory):
      for dirname in list(dirnames):
        dirabspath = os.path.join(dirpath, dirname)
        if any(fnmatch.fnmatch(
            dirabspath,
            pattern,
        ) for pattern in cls._save_instance_file_pattern_list):
          cls._copySnapshot(dirabspath, name)
          # don't recurse, since _copySnapshot is already recursive
          dirnames.remove(dirname)
      for filename in filenames:
        fileabspath = os.path.join(dirpath, filename)
        if any(fnmatch.fnmatch(
            fileabspath,
            pattern,
        ) for pattern in cls._save_instance_file_pattern_list):
          cls._copySnapshot(fileabspath, name)

  @classmethod
  def _storeSystemSnapshot(cls, name):
    """Store a snapshot of standalone slapos and partitions.

    Does not include software log, because this is stored at the end of software
    installation and software log is large.
    """
    # copy log files from standalone
    for standalone_log in glob.glob(os.path.join(
        cls._base_directory,
        'var',
        'log',
        '*',
    )):
      if not standalone_log.startswith('slapos-node-software.log'):
        cls._copySnapshot(standalone_log, name)
    # store slapproxy database
    cls._copySnapshot(cls.slap._proxy_database, name)
    cls._storePartitionSnapshot(name)

  def tearDown(self):
    self._storePartitionSnapshot(self.id())

  @classmethod
  def _copySnapshot(cls, source_file_name, name):
    """Save a file, symbolic link or directory for later inspection.

    The path are made relative to slapos root directory and
    we keep the same directory structure.
    """
    # we cannot use os.path.commonpath on python2, so implement something similar
    common_path = os.path.commonprefix((source_file_name, cls._base_directory))
    if not os.path.isdir(common_path):
      common_path = os.path.dirname(common_path)

    relative_path = source_file_name[len(common_path):]
    if relative_path[0] == os.sep:
      relative_path = relative_path[1:]
    destination = os.path.join(
        cls._test_file_snapshot_directory,
        cls.software_id,
        name,
        relative_path,
    )
    destination_dirname = os.path.dirname(destination)
    mkdir_p(destination_dirname)
    if os.path.islink(
        source_file_name) and not os.path.exists(source_file_name):
      cls.logger.debug(
          "copy broken symlink %s as %s", source_file_name, destination)
      with open(destination, 'w') as f:
        f.write('broken symink to {}\n'.format(os.readlink(source_file_name)))
    elif os.path.isfile(source_file_name):
      cls.logger.debug("copy %s as %s", source_file_name, destination)
      shutil.copy(source_file_name, destination)
    elif os.path.isdir(source_file_name):
      cls.logger.debug("copy directory %s as %s", source_file_name, destination)
      # we copy symlinks as symlinks, so that this does not fail when
      # we copy a directory containing broken symlinks.
      shutil.copytree(source_file_name, destination, symlinks=True)

  # implementation methods
  @classmethod
  def _cleanup(cls, snapshot_name):
    # type: (str) -> None
    """Destroy all instances and stop subsystem.
    Catches and log all exceptions and take snapshot named `snapshot_name` + the failing step.
    """
    try:
      cls.requestDefaultInstance(state='destroyed')
    except:
      cls.logger.exception("Error during request destruction")
      cls._storeSystemSnapshot(
          "{}._cleanup request destroy".format(snapshot_name))
    try:
      cls.slap.waitForReport(max_retry=cls.report_max_retry, debug=cls._debug)
    except:
      cls.logger.exception("Error during actual destruction")
      cls._storeSystemSnapshot(
          "{}._cleanup waitForReport".format(snapshot_name))
    leaked_partitions = [
        cp for cp in cls.slap.computer.getComputerPartitionList()
        if cp.getState() != 'destroyed'
    ]
    if leaked_partitions:
      cls.logger.critical(
          "The following partitions were not cleaned up: %s",
          [cp.getId() for cp in leaked_partitions])
      cls._storeSystemSnapshot(
          "{}._cleanup leaked_partitions".format(snapshot_name))
      for cp in leaked_partitions:
        try:
          # XXX is this really the reference ?
          partition_reference = cp.getInstanceParameterDict()['instance_title']
          cls.slap.request(
              software_release=cp.getSoftwareRelease().getURI(),
              # software_type=cp.getType(), # TODO
              partition_reference=partition_reference,
              state="destroyed")
        except:
          cls.logger.exception(
              "Error during request destruction of leaked partition")
          cls._storeSystemSnapshot(
              "{}._cleanup leaked_partitions request destruction".format(
                  snapshot_name))
      try:
        cls.slap.waitForReport(max_retry=cls.report_max_retry, debug=cls._debug)
      except:
        cls.logger.exception(
            "Error during leaked partitions actual destruction")
        cls._storeSystemSnapshot(
            "{}._cleanup leaked_partitions waitForReport".format(snapshot_name))
    try:
      cls.slap.stop()
    except:
      cls.logger.exception("Error during stop")
      cls._storeSystemSnapshot("{}._cleanup stop".format(snapshot_name))
    leaked_supervisor_configs = glob.glob(
        os.path.join(
            cls.slap.instance_directory, 'etc', 'supervisord.conf.d', '*.conf'))
    if leaked_supervisor_configs:
      for config in leaked_supervisor_configs:
        os.unlink(config)
      raise AssertionError(
          "Test leaked supervisor configurations: %s" %
          leaked_supervisor_configs)

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
