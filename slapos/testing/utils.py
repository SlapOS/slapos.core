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
