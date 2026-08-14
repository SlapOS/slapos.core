##############################################################################
#
# Copyright (c) 2013 Vifib SARL and Contributors. All Rights Reserved.
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
import unittest
from contextlib import closing

try:
  from unittest import mock
except ImportError:
  import mock

from slapos.testing.utils import findFreeTCPPortRange


class TestFindFreeTCPPortRange(unittest.TestCase):
  ip = '127.0.0.1'

  def _occupy(self, port=0):
    # bind a socket and keep it open for the test duration, so its port stays
    # occupied; return the bound port
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.addCleanup(s.close)
    s.bind((self.ip, port))
    return s.getsockname()[1]

  def _free_port(self):
    # a currently-free port (bound then released)
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
      s.bind((self.ip, 0))
      return s.getsockname()[1]

  def test_returns_consecutive_free_ports(self):
    base = findFreeTCPPortRange(self.ip, 3)
    self.assertIsInstance(base, int)
    # the returned range is free (bindable) and consecutive
    self.assertEqual(
      [base, base + 1, base + 2],
      [self._occupy(base + offset) for offset in range(3)])

  @mock.patch('slapos.testing.utils.random.randrange')
  def test_returns_first_free_range_without_exhausting_retries(self, randrange):
    free = self._free_port()
    occupied = self._occupy()
    # first candidate is free, every later candidate would collide: the free
    # range must be returned as soon as it is found, not decided only by the
    # last of the ten attempts
    randrange.side_effect = [free] + [occupied] * 9
    self.assertEqual(free, findFreeTCPPortRange(self.ip, 1))
    self.assertEqual(1, randrange.call_count)

  @mock.patch('slapos.testing.utils.random.randrange')
  def test_raises_when_no_free_range(self, randrange):
    occupied = self._occupy()
    randrange.side_effect = [occupied] * 10
    self.assertRaises(RuntimeError, findFreeTCPPortRange, self.ip, 1)


if __name__ == '__main__':
  unittest.main()
