# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2018 Nexedi SA and Contributors. All Rights Reserved.
#
# This program is free software: you can Use, Study, Modify and Redistribute
# it under the terms of the GNU General Public License version 3, or (at your
# option) any later version, as published by the Free Software Foundation.
#
# You can also Link and Combine this program with other software covered by
# the terms of any of the Free Software licenses or any of the Open Source
# Initiative approved licenses and Convey the resulting work. Corresponding
# source of such a combination shall include the source code for all other
# software used.
#
# This program is distributed WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See COPYING file for full licensing terms.
# See https://www.nexedi.com/licensing for rationale and options.
#
##############################################################################

import socket
import hashlib
import unittest
import os
import subprocess
import sys
import json
from contextlib import closing

try:
  import typing
  if typing.TYPE_CHECKING:
    from PIL import Image # pylint:disable=unused-import
except ImportError:
  pass


# Utility functions
def findFreeTCPPort(ip=''):
  # type: (str) -> int
  """Find a free TCP port to listen to.
  """
  s = socket.socket(
      socket.AF_INET6 if ':' in ip else socket.AF_INET, socket.SOCK_STREAM)
  with closing(s):
    s.bind((ip, 0))
    return s.getsockname()[1]


def getPortFromPath(path):
  # type: (str) -> int
  """A stable port using a hash from path.
  """
  return 1024 + int(
      hashlib.md5(path.encode('utf-8', 'backslashreplace')).hexdigest(),
      16) % (65535 - 1024)


def getPromisePluginParameterDict(filepath):
  # type: (str) -> dict
  """Load the slapos monitor plugin and returns the configuration used by this plugin.

  This allow to check that monitoring plugin are using a proper config.
  """
  extra_config_dict_json = subprocess.check_output([
      sys.executable,
      "-c",
      """
import json, sys
with open(sys.argv[1]) as f:
  exec(f.read())
print(json.dumps(extra_config_dict))
""",
      filepath,
  ])
  return json.loads(extra_config_dict_json)


class CrontabMixin(object):
  computer_partition_root_path = None # type: str
  def _getCrontabCommand(self, crontab_name):
    # type: (str) -> str
    """Read a crontab and return the command that is executed.
    """
    with open(
        os.path.join(
            self.computer_partition_root_path,
            'etc',
            'cron.d',
            crontab_name,
        )) as f:
      crontab_spec = f.read()
    return " ".join(crontab_spec.split()[5:])

  def _executeCrontabAtDate(self, crontab_name, date):
    # type: (str, str) -> None
    """Executes a crontab as if the current date was `date`.

    `date` will be passed to faketime time command, it can also
    be a relative time.
    """
    crontab_command =  self._getCrontabCommand(crontab_name)
    subprocess.check_call(
        "faketime {date} bash -o pipefail -e -c '{crontab_command}'".format(**locals()),
        shell=True,
    )


class ImageComparisonTestCase(unittest.TestCase):
  """TestCase with utility method to compare images.

  The images must be passed as instances of `PIL.Image`
  """
  def assertImagesSimilar(self, i1, i2, tolerance=5):
    # type: (Image, Image, float) -> None
    """Assert images difference between images is less than `tolerance` %.
    taken from https://rosettacode.org/wiki/Percentage_difference_between_images
    """
    pairs = zip(i1.getdata(), i2.getdata())
    if len(i1.getbands()) == 1:
      # for gray-scale jpegs
      dif = sum(abs(p1 - p2) for p1, p2 in pairs)
    else:
      dif = sum(abs(c1 - c2) for p1, p2 in pairs for c1, c2 in zip(p1, p2))

    ncomponents = i1.size[0] * i1.size[1] * 3
    self.assertLessEqual((dif / 255.0 * 100) / ncomponents, tolerance)

  def assertImagesSame(self, i1, i2):
    # type: (Image, Image) -> None
    """Assert images are exactly same."""
    self.assertImagesSimilar(i1, i2, 0)
