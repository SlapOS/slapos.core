# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2010-2014 Vifib SARL and Contributors.
# All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsibility of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# guarantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public License
# as published by the Free Software Foundation; either version 2.1
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

import errno
import os
import socket
import struct
import subprocess
import sqlite3
from xml_marshaller.xml_marshaller import dumps, loads


def mkdir_p(path, mode=0o700):
    """\
    Creates a directory and its parents, if needed.

    NB: If the directory already exists, it does not change its permission.
    """

    try:
        os.makedirs(path, mode)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def chownDirectory(path, uid, gid):
  if os.getuid() != 0:
    # we are probably inside of a webrunner
    return
  # find /opt/slapgrid -not -user 1000 -exec chown slapsoft:slapsoft {} +
  subprocess.check_call([
      '/usr/bin/find', path, '-not', '-user', str(uid), '-exec',
      '/bin/chown', '%s:%s' % (uid, gid), '{}', '+'
  ])


def parse_certificate_key_pair(html):
  """
  Extract (certificate, key) pair from an HTML page received by SlapOS Master.
  """

  c_start = html.find("Certificate:")
  c_end = html.find("</textarea>", c_start)
  certificate = html[c_start:c_end]

  k_start = html.find("-----BEGIN PRIVATE KEY-----")
  k_end = html.find("</textarea>", k_start)
  key = html[k_start:k_end]

  return certificate, key


def string_to_boolean(string):
  """
  Return True if the value of the "string" parameter can be parsed as True.
  Return False if the value of the "string" parameter can be parsed as False.
  Otherwise, Raise.

  The parser is completely arbitrary, see code for actual implementation.
  """
  try:
    return ('false', 'true').index(string.lower())
  except Exception:
    raise ValueError('%s is neither True nor False.' % string)


def sqlite_connect(dburi, timeout=None):
  connect_kw = {}
  if timeout is not None:
    connect_kw['timeout'] = timeout
  conn = sqlite3.connect(dburi, **connect_kw)
  conn.text_factory = str       # allow 8-bit strings
  return conn

# The 3 functions below were imported from re6st:
# https://lab.nexedi.com/nexedi/re6stnet/blob/master/re6st/utils.py
def binFromRawIpv6(ip):
  ip1, ip2 = struct.unpack('>QQ', ip)
  return bin(ip1)[2:].rjust(64, '0') + bin(ip2)[2:].rjust(64, '0')

def binFromIpv6(ip):
  """
  convert an IPv6  to a 128 characters string containing 0 and 1
  e.g.: '2001:db8::'-> '001000000000000100001101101110000000000...000'
  """
  return binFromRawIpv6(socket.inet_pton(socket.AF_INET6, ip))

def ipv6FromBin(ip, suffix=''):
  """
  convert a string containing 0 and 1 to an IPv6
  if the string is less than 128 characters:
   * consider the string is the first bits
   * optionnaly can replace the last bits of the IP with a suffix (in binary string format)
  """
  suffix_len = 128 - len(ip)
  if suffix_len > 0:
    ip += suffix.rjust(suffix_len, '0')
  elif suffix_len:
    sys.exit("Prefix exceeds 128 bits")
  return socket.inet_ntop(socket.AF_INET6,
    struct.pack('>QQ', int(ip[:64], 2), int(ip[64:], 2)))

def lenNetmaskIpv6(netmask):
  return len(binFromIpv6(netmask).rstrip('0'))

# Used for Python 2-3 compatibility
if str is bytes:
  bytes2str = str2bytes = lambda s: s
  def unicode2str(s):
    return s.encode('utf-8')
else:
  def bytes2str(s):
    return s.decode()
  def str2bytes(s):
    return s.encode()
  def unicode2str(s):
    return s
