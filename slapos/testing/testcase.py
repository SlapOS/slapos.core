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

from __future__ import annotations
import contextlib
import fnmatch
import glob
import logging
import os
import shutil
import sqlite3
import unittest
import warnings

from six.moves.urllib.parse import urlparse

from netaddr import valid_ipv6

from .utils import getPortFromPath
from .utils import ManagedResource

from ..slap.standalone import StandaloneSlapOS
from ..slap.standalone import SlapOSNodeCommandError
from ..slap.standalone import PathTooDeepError

from ..util import mkdir_p
from ..slap import ComputerPartition
from .check_software import checkSoftware

from ..proxy.db_version import DB_VERSION

from typing import (
  Callable,
  ClassVar,
  Dict,
  Iterable,
  List,
  Mapping,
  Optional,
  Sequence,
  Tuple,
  Type,
  TypeVar,
)
ManagedResourceType = TypeVar("ManagedResourceType", bound=ManagedResource)

IPV4_ADDRESS_DEFAULT: str = os.environ['SLAPOS_TEST_IPV4']
IPV6_ADDRESS_DEFAULT: str = os.environ['SLAPOS_TEST_IPV6']
DEBUG_DEFAULT: bool = bool(
  int(os.environ.get('SLAPOS_TEST_DEBUG', 0)),
)
VERBOSE_DEFAULT: bool = bool(
  int(os.environ.get('SLAPOS_TEST_VERBOSE', 0)),
)
SKIP_SOFTWARE_CHECK_DEFAULT: bool = bool(
  int(os.environ.get('SLAPOS_TEST_SKIP_SOFTWARE_CHECK', 0))
)
SKIP_SOFTWARE_REBUILD_DEFAULT: bool = bool(
  int(os.environ.get('SLAPOS_TEST_SKIP_SOFTWARE_REBUILD', 0))
)
SHARED_PART_LIST_DEFAULT: Sequence[str] = [
  os.path.expanduser(p)
  for p in os.environ.get(
    'SLAPOS_TEST_SHARED_PART_LIST',
    '',
  ).split(os.pathsep) if p
]
SNAPSHOT_DIRECTORY_DEFAULT: str | None = os.environ.get(
  'SLAPOS_TEST_LOG_DIRECTORY',
)

def makeModuleSetUpAndTestCaseClass(
  software_url: str,
  *,
  base_directory: str | None = None,
  ipv4_address: str = IPV4_ADDRESS_DEFAULT,
  ipv6_address: str = IPV6_ADDRESS_DEFAULT,
  debug: bool = DEBUG_DEFAULT,
  verbose: bool = VERBOSE_DEFAULT,
  skip_software_check: bool = SKIP_SOFTWARE_CHECK_DEFAULT,
  skip_software_rebuild: bool = SKIP_SOFTWARE_REBUILD_DEFAULT,
  shared_part_list: Iterable[str] = SHARED_PART_LIST_DEFAULT,
  snapshot_directory: str | None = SNAPSHOT_DIRECTORY_DEFAULT,
  software_id: str | None = None
) -> Tuple[Callable[[], None], Type[SlapOSInstanceTestCase]]:
  """
  Create a setup module function and a testcase for testing `software_url`.

  Note:
    SlapOS itself and some services running in SlapOS uses unix sockets and
    (sometimes very) deep paths, which do not play very well together.
    To workaround this, users can set ``SLAPOS_TEST_WORKING_DIR`` environment
    variable to the path of a short enough directory and local slapos will
    use this directory.
    The partitions references will be named after the unittest class name,
    which can also lead to long paths. For this, unit test classes can define
    a ``__partition_reference__`` attribute which will be used as partition
    reference. If the class names are long, the trick is then to use a shorter
    ``__partition_reference__``.
    See https://lab.nexedi.com/kirr/slapns for a solution to this problem.

  Args:
    software_url: The URL of the software to test.
    base_directory: The base directory used for SlapOS.
      By default, it will use the value in the environment variable
      ``SLAPOS_TEST_WORKING_DIR``.
      If that is not defined, it will default to ``.slapos`` in the current
      directory.
    ipv4_address: IPv4 address used for the instance. By default it will use
      the one defined in the environment variable ``SLAPOS_TEST_IPV4``.
    ipv6_address: IPv6 address used for the instance. By default it will use
      the one defined in the environment variable ``SLAPOS_TEST_IPV6``.
    debug: Enable debugging mode, which will drop in a debugger session when
      errors occur.
      By default it will be controlled by the value of the environment variable
      ``SLAPOS_TEST_DEBUG`` if it is defined. Otherwise it will be disabled.
    verbose: ``True`` to enable verbose logging, so that the test framework
      logs information describing the actions taken (sets logging level to
      ``DEBUG``).
      By default it will be controlled by the value of the environment variable
      ``SLAPOS_TEST_VERBOSE`` if it is defined. Otherwise it will be disabled.      
    skip_software_check: Skips costly software checks.
      By default it will be controlled by the value of the environment variable
      ``SLAPOS_TEST_SKIP_SOFTWARE_CHECK`` if it is defined. Otherwise it will
      be disabled.
    skip_software_rebuild: Skips costly software builds.
      By default it will be controlled by the value of the environment variable
      ``SLAPOS_TEST_SKIP_SOFTWARE_REBUILD`` if it is defined. Otherwise it will
      be disabled.
    shared_part_list: Additional paths to search for existing shared parts.
      This test class will use its own directory for shared parts and also
      the paths defined in this argument.
      By default it is controlled by the ``SLAPOS_TEST_SHARED_PART_LIST``
      environment variable if defined, which should contain the paths in a
      string separated by colons (':').
    snapshot_directory: Directory to save snapshot files (for further
      inspection) and logs.
      If it is ``None`` or the empty string, logs will be stored in
      ``base_directory``, and no snapshots will be stored.
      By default it will use the value of the environment variable
      ``SLAPOS_TEST_LOG_DIRECTORY`` if it is defined, and ``None`` otherwise.
    software_id: A short name for the software, to be used in logs and to
      name the snapshots.
      By default it is computed automatically from the software URL, but can
      also be passed explicitly, to use a different name for different kind of
      tests, like for example upgrade tests.

  Returns:
    A tuple of two arguments:
      - A function to install the software, to be used as `unittest`'s
        `setUpModule`.
      - A base class for test cases.
  
  """
  if base_directory is None:
    base_directory = os.path.realpath(
      os.environ.get(
        'SLAPOS_TEST_WORKING_DIR',
        os.path.join(
          os.getcwd(),
          '.slapos',
        )
      )
    )

  if not software_id:
    software_id = urlparse(software_url).path.split('/')[-2]

  logging.basicConfig(
    level=logging.DEBUG,
    format=f'%(asctime)s - {software_id} - %(name)s - %(levelname)s - %(message)s',
    filename=os.path.join(
      snapshot_directory or base_directory,
      'testcase.log',
    ),
  )
  logger = logging.getLogger()
  console_handler = logging.StreamHandler()
  console_handler.setLevel(
    logging.DEBUG if verbose else logging.WARNING,
  )
  logger.addHandler(console_handler)

  if debug:
    unittest.installHandler()

  # TODO: fail if already running ?
  try:
    slap = StandaloneSlapOS(
      base_directory=base_directory,
      server_ip=ipv4_address,
      server_port=getPortFromPath(base_directory),
      shared_part_list=shared_part_list,
    )
  except PathTooDeepError:
    raise RuntimeError(
      f'base directory ( {base_directory} ) is too deep, try setting '
      f'SLAPOS_TEST_WORKING_DIR to a shallow enough directory',
    )

  cls = type(
    f'SlapOSInstanceTestCase for {software_url}',
    (SlapOSInstanceTestCase,),
    {
      'slap': slap,
      'getSoftwareURL': classmethod(lambda _cls: software_url),
      'software_id': software_id,
      '_debug': debug,
      '_skip_software_check': skip_software_check,
      '_skip_software_rebuild': skip_software_rebuild,
      '_ipv4_address': ipv4_address,
      '_ipv6_address': ipv6_address,
      '_base_directory': base_directory,
      '_test_file_snapshot_directory': snapshot_directory
    },
  )

  class SlapOSInstanceTestCase_(
    cls,  # type: ignore # https://github.com/python/mypy/issues/2813
    SlapOSInstanceTestCase,
  ):
    # useless intermediate class so that editors provide completion anyway.
    pass

  def setUpModule() -> None:
    installSoftwareUrlList(cls, [software_url], debug=debug)

  return setUpModule, SlapOSInstanceTestCase_


def installSoftwareUrlList(cls, software_url_list, max_retry=10, debug=False):
  # type: (Type[SlapOSInstanceTestCase], Iterable[str], int, bool) -> None
  """Install softwares on the current testing slapos, for use in `setUpModule`.

  This also check softwares with `checkSoftware`
  """
  def _storeSoftwareSnapshot(name):
    for path in glob.glob(os.path.join(
        cls._base_directory,
        'var',
        'log',
        '*',
    )) + glob.glob(os.path.join(
        cls.slap.software_directory,
        '*',
        '*.cfg',
    )) + glob.glob(os.path.join(
        cls.slap.software_directory,
        '*',
        '.installed.cfg',
    )) + glob.glob(os.path.join(
        cls.slap.shared_directory,
        '*',
        '*',
        '.slapos.recipe.cmmi.signature',
    )):
      cls._copySnapshot(path, name)

  try:
    cls.logger.debug("Starting SlapOS")
    cls.slap.start()
    for software_url in software_url_list:
      cls.logger.debug("Supplying %s", software_url)
      cls.slap.supply(software_url)
    cls.logger.debug("Waiting for slapos node software to build")
    cls.slap.waitForSoftware(max_retry=max_retry, debug=debug, install_all=not cls._skip_software_rebuild)
    _storeSoftwareSnapshot('setupModule')
    if not cls._skip_software_check:
      for software_url in software_url_list:
        cls.logger.debug("Checking software %s", software_url)
        checkSoftware(cls.slap, software_url)
        cls.logger.debug("Done checking software %s", software_url)
    else:
      cls.logger.debug("Software checks skipped")

  except BaseException as e:
    _storeSoftwareSnapshot('setupModule failed installing software')
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
        _storeSoftwareSnapshot('setupModule removing software')
    cls._cleanup('setupModule')
    raise


class SlapOSInstanceTestCase(unittest.TestCase):
  """
  Install one slapos instance.

  This test case install software(s) and request one instance
  during `setUpClass` and destroy that instance during `tearDownClass`.

  Software Release URL, Instance Software Type and Instance Parameters
  can be defined on the class.

  All tests from the test class will run with the same instance.

  Note:
    This class is not supposed to be imported directly, but needs to be setup
    by calling makeModuleSetUpAndTestCaseClass.

  Attributes:
    computer_partition: The computer partition instance.
    computer_partition_root_path: The path of the instance root directory.
    computer_partition_ipv6_address: The IPv6 of the instance.
    instance_max_retry: Maximum retries for ``slapos node instance``.
    report_max_retry: Maximum retries for ``slapos node report``.
    partition_count: Number of partitions needed for this instance.
    default_partition_reference: Reference of the default requested partition.
    request_instance: Whether an instance needs to be requested for this test
        case.
    software_id: A short name of that software URL. E.g. helloworld instead of
        https://lab.nexedi.com/nexedi/slapos/raw/software/helloworld/software.cfg .
    logger: A logger for messages of the testing framework.
    slap: Standalone SlapOS instance.
  """

  instance_max_retry: ClassVar[int] = 20
  report_max_retry: ClassVar[int] = 20
  partition_count: ClassVar[int] = 10
  default_partition_reference: ClassVar[str] = 'testing partition 0'
  request_instance: ClassVar[bool] = True
  software_id: ClassVar[str] = ""

  logger: ClassVar[logging.Logger] = logging.getLogger(__name__)

  # Dynamic members
  slap: ClassVar[StandaloneSlapOS]
  computer_partition: ClassVar[ComputerPartition]
  computer_partition_root_path: ClassVar[str]
  computer_partition_ipv6_address: ClassVar[str]


  # Private settings

  # True to enable debugging utilities.
  _debug: ClassVar[bool] = False

  # True to skip software checks.
  _skip_software_check: ClassVar[bool] = False

  # True to skip software rebuild.
  _skip_software_rebuild: ClassVar[bool] = False

  # The IPv4 address used by ``slapos node format``.
  _ipv4_address: ClassVar[str] = ""

  # The IPv6 address used by ``slapos node format``.
  _ipv6_address: ClassVar[str] = ""

  # Used resources.
  _resources: ClassVar[Dict[str, ManagedResource]] = {}

  # Instance parameters
  _instance_parameter_dict: ClassVar[Mapping[str, object]]

  # Base directory for standalone SlapOS.
  _base_directory: ClassVar[str] = ""  

  # Directory to save snapshot files for inspections.
  _test_file_snapshot_directory: ClassVar[str | None] = ""

  # Patterns of files to save for inspection, relative to instance directory.
  _save_instance_file_pattern_list: ClassVar[Sequence[str]] = (
      '*/bin/*',
      '*/etc/*',
      '*/var/log/*',
      '*/srv/monitor/*',
      '*/srv/backup/logrotate/*',
      '*/.*log',
      '*/.*cfg',
      '*/*cfg',
      'etc/',
  )

  @classmethod
  def getManagedResource(cls, resource_name, resource_class):
    # type: (str, Type[ManagedResourceType]) -> ManagedResourceType
    """Get the managed resource for this name.

    If resource was not created yet, it is created and `open`. The
    resource will automatically be `close` at the end of the test
    class.
    """
    try:
      existing_resource = cls._resources[resource_name]
    except KeyError:
      resource = resource_class(cls, resource_name)
      cls._resources[resource_name] = resource
      resource.open()
      return resource
    else:
      if not isinstance(existing_resource, resource_class):
        raise ValueError(
            "Resource %s is of unexpected class %s" %
            (resource_name, existing_resource), )
      return existing_resource

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
    """Return software type for instance, default None.

    To be defined by subclasses if they need to request instance with specific
    software type.
    """
    return None

  # Unittest methods
  @classmethod
  def waitForInstance(cls):
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

  @classmethod
  def formatPartitions(cls):
    cls.logger.debug(
        "Formatting to remove old partitions XXX should not be needed because we delete ..."
    )
    cls.slap.format(0, cls._ipv4_address, cls._ipv6_address)
    cls.logger.debug("Formatting with %s partitions", cls.partition_count)
    cls.slap.format(
        cls.partition_count, cls._ipv4_address, cls._ipv6_address,
        getattr(cls, '__partition_reference__', '{}-'.format(cls.__name__)))

  @classmethod
  def _setUpClass(cls) -> None:
    cls.slap.start()

    # (re)format partitions
    cls.formatPartitions()

    # request
    if cls.request_instance:
      cls.requestDefaultInstance()

      # slapos node instance
      cls.logger.debug("Waiting for instance")
      cls.waitForInstance()

      # expose some class attributes so that tests can use them:
      # the main ComputerPartition instance, to use getInstanceParameterDict
      cls.computer_partition = cls.requestDefaultInstance()

      # the path of the instance on the filesystem, for low level inspection
      cls.computer_partition_root_path = os.path.join(
        cls.slap._instance_root,
        cls.computer_partition.getId(),
      )

      # the ipv6 of the instance
      cls.computer_partition_ipv6_address = cls.getPartitionIPv6(
        cls.computer_partition.getId(),
      )

  @classmethod
  @contextlib.contextmanager
  def _snapshotManager(cls, snapshot_name):
    try:
      yield
    except BaseException:
      cls._storeSystemSnapshot(snapshot_name)
      cls._cleanup(snapshot_name)
      raise
    else:
      cls._storeSystemSnapshot(snapshot_name)

  @classmethod
  def setUpClass(cls):
    """Request an instance.
    """
    cls.logger.debug("Starting setUpClass %s", cls)
    cls._instance_parameter_dict = cls.getInstanceParameterDict()
    snapshot_name = "{}.{}.setUpClass".format(cls.__module__, cls.__name__)

    with cls._snapshotManager(snapshot_name):
      try:
        cls._setUpClass()
      except BaseException:
        cls.logger.exception("Error during setUpClass")
        cls.setUp = lambda self: self.fail('Setup Class failed.')
        raise
    cls.logger.debug("setUpClass done")

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
    if not cls._test_file_snapshot_directory:
      warnings.warn("No snapshot directory configured, skipping snapshot")
      warnings.warn("Snapshot directory can be configured with SLAPOS_TEST_LOG_DIRECTORY environment")
      return
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
      shutil.copy(source_file_name, destination)
    elif os.path.isdir(source_file_name):
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
    for resource_name in list(cls._resources):
      cls.logger.debug("closing resource %s", resource_name)
      try:
        cls._resources.pop(resource_name).close()
      except:
        cls.logger.exception("Error closing resource %s", resource_name)
    try:
      if cls.request_instance and hasattr(cls, '_instance_parameter_dict'):
        cls.requestDefaultInstance(state='destroyed')
    except:
      cls.logger.exception("Error during request destruction")
      cls._storeSystemSnapshot(
          "{}._cleanup request destroy".format(snapshot_name))
    try:
      # To make debug usable, we tolerate report_max_retry-1 errors and
      # only debug the last.
      for _ in range(3):
        if cls._debug and cls.report_max_retry:
          try:
            cls.slap.waitForReport(max_retry=cls.report_max_retry - 1)
          except SlapOSNodeCommandError:
            cls.slap.waitForReport(debug=True)
        else:
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
        # To make debug usable, we tolerate report_max_retry-1 errors and
        # only debug the last.
        for _ in range(3):
          if cls._debug and cls.report_max_retry:
            try:
              cls.slap.waitForReport(max_retry=cls.report_max_retry - 1)
            except SlapOSNodeCommandError:
              cls.slap.waitForReport(debug=True)
          else:
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
        'requesting "%s" software:%s type:%r state:%s parameters:%s',
        cls.default_partition_reference, software_url, software_type, state,
        cls._instance_parameter_dict)
    return cls.slap.request(
        software_release=software_url,
        software_type=software_type,
        partition_reference=cls.default_partition_reference,
        partition_parameter_kw=cls._instance_parameter_dict,
        state=state)

  @classmethod
  def getPartitionId(cls, instance_name):
    query = "SELECT reference FROM partition%s WHERE partition_reference=?" % DB_VERSION
    with sqlite3.connect(os.path.join(
      cls._base_directory,
      'var/proxy.db',
    )) as db:
      return db.execute(query, (instance_name,)).fetchall()[0][0]

  @classmethod
  def getPartitionIPv6(cls, partition_id):
    query = "SELECT address FROM partition_network%s WHERE partition_reference=?" % DB_VERSION
    with sqlite3.connect(os.path.join(
      cls._base_directory,
      'var/proxy.db',
    )) as db:
      rows = db.execute(query, (partition_id,)).fetchall()
    # do not assume the partition's IPv6 address is the second one,
    # instead find the first address that is IPv6
    for (address,) in rows:
      if valid_ipv6(address):
        return address
