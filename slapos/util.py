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
import json
from xml_marshaller.xml_marshaller import dumps, loads
from lxml import etree
import six
from six.moves.urllib import parse
import hashlib
import netaddr


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


def sqlite_connect(dburi, timeout=None, isolation_level=None):
  connect_kw = {}
  if timeout is not None:
    connect_kw['timeout'] = timeout
  
  connect_kw['isolation_level'] = isolation_level
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
  """Convert string represented netmask to its integer prefix"""
  # Since version 0.10.7 of netifaces, the netmask is something like "ffff::/16",
  # (it used to be "ffff::"). For old versions of netifaces, interpret the netmask
  # as an address and return its netmask, but for newer versions returns the prefixlen.
  try:
    return netaddr.IPAddress(netmask).netmask_bits()
  except ValueError:
    return netaddr.IPNetwork(netmask).prefixlen

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


def dict2xml(dictionary):
  instance = etree.Element('instance')
  if len(dictionary) == 1 and '_' in dictionary:
    etree.SubElement(instance, "parameter",
            attrib={'id': '_'}).text = json.dumps(
                    dictionary['_'],
                    separators=(',', ': '),
                    sort_keys=True,
                    indent=4)
  else:
    for k, v in sorted(six.iteritems(dictionary)):
      if isinstance(k, bytes):
        k = k.decode('utf-8')
      if isinstance(v, bytes):
        v = v.decode('utf-8')
      elif not isinstance(v, six.text_type):
        v = str(v)
      etree.SubElement(instance, "parameter",
                     attrib={'id': k}).text = v
  return bytes2str(etree.tostring(instance,
                   pretty_print=True,
                   xml_declaration=True,
                   encoding='utf-8'))


def xml2dict(xml):
  result_dict = {}
  if xml:
    tree = etree.fromstring(str2bytes(xml))
    for element in tree.iterfind('parameter'):
      key = element.get('id')
      value = result_dict.get(key, None)
      if value is not None:
        value = value + ' ' + element.text
      else:
        value = element.text
      result_dict[key] = value
  if len(result_dict) == 1 and '_' in result_dict:
    result_dict['_'] = json.loads(result_dict['_'])
  return result_dict


def calculate_dict_hash(d):
  return hashlib.sha256(
    str2bytes(str(
      sorted(
        d.items()
      )
    ))).hexdigest()


def _addIpv6Brackets(url):
  # if master_url contains an ipv6 without bracket, add it
  # Note that this is mostly to limit specific issues with
  # backward compatiblity, not to ensure generic detection.
  api_scheme, api_netloc, api_path, api_query, api_fragment = parse.urlsplit(url)
  try:
    ip = netaddr.IPAddress(api_netloc)
    port = None
  except netaddr.AddrFormatError:
    try:
      ip = netaddr.IPAddress(':'.join(api_netloc.split(':')[:-1]))
      port = api_netloc.split(':')[-1]
    except netaddr.AddrFormatError:
      ip = port = None
  if ip and ip.version == 6:
    api_netloc = '[%s]' % ip
    if port:
      api_netloc = '%s:%s' % (api_netloc, port)
    url = parse.urlunsplit((api_scheme, api_netloc, api_path, api_query, api_fragment))
  return url
