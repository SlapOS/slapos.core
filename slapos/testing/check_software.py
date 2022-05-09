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

import fnmatch
import glob
import os
import re
import warnings

import pkg_resources
import requests
from six.moves.configparser import ConfigParser
import six

try:
  import subprocess32 as subprocess
except ImportError:
  import subprocess  # type: ignore
  subprocess  # pyflakes

try:
  from typing import  Dict, Iterable, List
except ImportError:
  pass

from ..slap.standalone import StandaloneSlapOS
from ..grid.utils import md5digest


def checkSoftware(slap, software_url):
  # type: (StandaloneSlapOS, str) -> None
  """Check software installation.

  This perform a few basic static checks for common problems
  with software installations.
  """
  # Check that all components set rpath correctly and we don't have miss linking any libraries.
  # Also check that they are not linked against system libraries, except a list of core
  # system libraries.
  system_lib_allowed_list = set((
      'libanl',
      'libc',
      'libcrypt',
      'libdl',
      'libgcc_s',
      'libgomp',
      'libm',
      'libnsl',
      'libpthread',
      'libthread_db',
      'libresolv',
      'librt',
      'libstdc++',
      'libutil',
  ))

  # Some libraries might also not be found statically but provided at run time.
  missing_lib_allowed_list = set((
      # references to liblibgolang.so from projects outside of pygolang are resolved at runtime for now.
      # https://github.com/mdavidsaver/setuptools_dso/issues/11#issuecomment-808258994
      'liblibgolang',
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
      # R uses wrappers to relocate symbols
      '*/r-language/lib*/R/*',
      # pulp is a git checkout with some executables
      '*/pulp-repository.git/src/pulp/solverdir/cbc*',
      # nss is not a binary distribution, but for some reason it has invalid rpath, but it does
      # not seem to be a problem in our use cases.
      '*/parts/nss/*',
      # npm packages containing binaries
      '*/node_modules/phantomjs*/*',
      '*/grafana/tools/phantomjs/*',
      '*/node_modules/puppeteer/*',
      # left over of compilation failures
      '*/*__compile__/*',
      # build dir for packages built in-place
      '*/parts/wendelin.core/build/*',
      # the depot_tools package used to build Chromium installs some
      # Python libraries lacking an rpath; these are not actually used
      # by Chromium itself
      '*/.vpython-root/*',
  ))

  software_hash = md5digest(software_url)
  error_list = []
  warning_list = []

  ldd_so_resolved_re = re.compile(
      r'\t(?P<library_name>.*) => (?P<library_path>.*) \(0x')
  ldd_already_loaded_re = re.compile(r'\t(?P<library_name>.*) \(0x')
  ldd_not_found_re = re.compile(r'\t(?P<library_name>.*) => not found.*')

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
        library_name = not_found_match.group('library_name')
        if library_name.split('.')[0] not in missing_lib_allowed_list:
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
    valid_paths_for_libs = [os.path.realpath(x) for x in valid_paths_for_libs]
    executable_link_error_list = []
    for path in paths_to_check:
      for root, dirs, files in os.walk(path):
        for f in files:
          f = os.path.join(root, f)
          if any(fnmatch.fnmatch(f, ignored_pattern)
                 for ignored_pattern in ignored_file_patterns):
            continue
          if os.access(f, os.X_OK) or fnmatch.fnmatch(f, '*.so'):
            try:
              libs = getLddOutput(f)
            except DynamicLibraryNotFound as e:
              executable_link_error_list.append(str(e))
            else:
              for lib, lib_path in libs.items():
                if lib.split('.')[0] in system_lib_allowed_list:
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

  software_directory = os.path.join(slap.software_directory, software_hash)
  paths_to_check = set((software_directory, ))

  # Compute the paths to check by inspecting buildout installed database
  # for this software. We are looking for shared parts installed by recipes.
  config_parser = ConfigParser()
  config_parser.read(os.path.join(software_directory, '.installed.cfg'))
  for section_name in config_parser.sections():
    for option_name in 'location', '__buildout_installed__':
      if config_parser.has_option(section_name, option_name):
        for section_path in config_parser.get(section_name, option_name).splitlines():
          if section_path and not section_path.startswith(software_directory):
            paths_to_check.add(section_path)

  error_list.extend(
      checkExecutableLink(
          paths_to_check,
          tuple(paths_to_check) + tuple(slap._shared_part_list),
      ))

  # check this software is not referenced in any shared parts.
  for signature_file in glob.glob(
      os.path.join(
          slap.shared_directory,
          '*',
          '*',
          '.buildout-shared.json',
      )):
    with open(signature_file) as f:
      signature_content = f.read()
    if software_hash in signature_content:
      error_list.append(
          "Shared part is referencing non shared part or software {}\n{}\n".format(
              signature_file, signature_content))

  def checkEggsVersionsKnownVulnerabilities(
      egg_directories,
      safety_db=requests.get(
          'https://raw.githubusercontent.com/pyupio/safety-db/master/data/insecure_full.json'
      ).json()):
    # type: (List[str], Dict) -> Iterable[str]
    """Check eggs against known vulnerabilities database from https://github.com/pyupio/safety-db
    """
    def get_python_versions():
      # () -> Iterable[str]
      """Returns all python versions used in egg_directories 
      """
      python_versions = set()
      for egg_dir in egg_directories:
        basename, _ = os.path.splitext(os.path.basename(egg_dir))
        match = pkg_resources.EGG_NAME(basename)
        if match:
          pyver = match.group('pyver')
          if pyver:
            python_versions.add(pyver)
      return python_versions

    for python in get_python_versions():
      env = pkg_resources.Environment(egg_directories, python=python)
      for egg in env:
        known_vulnerabilities = safety_db.get(egg)
        if known_vulnerabilities:
          for distribution in env[egg]:
            for known_vulnerability in known_vulnerabilities:
              for vulnerable_spec in known_vulnerability['specs']:
                for req in pkg_resources.parse_requirements(egg +
                                                            vulnerable_spec):
                  vulnerability_description = "\n".join(
                      u"{}: {}".format(*item)
                      for item in known_vulnerability.items())
                  if distribution in req:
                    yield (
                        u"{egg} use vulnerable version {distribution.version} because {vulnerable_spec}.\n"
                        "{vulnerability_description}\n".format(**locals()))

  warning_list.extend(
      checkEggsVersionsKnownVulnerabilities(
          glob.glob(
              os.path.join(
                  slap.software_directory,
                  software_hash,
                  'eggs',
                  '*',
              )) + glob.glob(
                  os.path.join(
                      slap.software_directory,
                      software_hash,
                      'develop-eggs',
                      '*',
                  ))))

  if warning_list:
    if six.PY2:
      # https://bugs.python.org/issue34752
      warnings.warn('\n'.join(warning_list).encode('utf-8'))
    else:
      warnings.warn('\n'.join(warning_list))
  if error_list:
    raise RuntimeError('\n'.join(error_list))
