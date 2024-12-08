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

import enum
import errno
import hashlib
import json
import logging
import os
import pprint
import shutil
import socket
import sqlite3
import struct
import subprocess
import sys
import warnings

import jsonschema
import netaddr
import zc.buildout.download
import six
from lxml import etree
from six.moves.urllib import parse
from six.moves.urllib_parse import urljoin
from xml_marshaller.xml_marshaller import Marshaller, Unmarshaller

try:
  from typing import Dict, Iterator, List, Optional
except ImportError:
  pass



try:
  PermissionError
except NameError:  # make pylint happy on python2...
  PermissionError = Exception



_ALLOWED_CLASS_SET = frozenset((
    ('slapos.slap.slap', 'Computer'),
    ('slapos.slap.slap', 'ComputerPartition'),
    ('slapos.slap.slap', 'SoftwareRelease'),
    ('slapos.slap.slap', 'SoftwareInstance'),
))


class SafeXMLMarshaller(Marshaller):
  def m_instance(self, value, kw):
    cls = value.__class__
    if (cls.__module__, cls.__name__) in _ALLOWED_CLASS_SET:
      return super(SafeXMLMarshaller, self).m_instance(value, kw)
    raise RuntimeError("Refusing to marshall {}.{}".format(
        cls.__module__, cls.__name__))


dumps = SafeXMLMarshaller().dumps


class SafeXMLUnmrshaller(Unmarshaller, object):
  def find_class(self, module, name):
    if (module, name) in _ALLOWED_CLASS_SET:
      return super(SafeXMLUnmrshaller, self).find_class(module, name)
    raise RuntimeError("Refusing to unmarshall {}.{}".format(module, name))


loads = SafeXMLUnmrshaller().loads


def mkdir_p(
  path, # type: str
  mode=0o700, # type: int
):
    # type: (...) -> None
    """
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


def listifdir(path):
  """
  Like listdir, but returns an empty tuple if the path is not a directory.
  """
  try:
    return os.listdir(path)
  except OSError as e:
    if e.errno != errno.ENOENT:
      raise
    return ()


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
    sys.exit("Prefix %s exceeds 128 bits by %d bit" % (ip, -suffix_len))
  return socket.inet_ntop(socket.AF_INET6,
    struct.pack('>QQ', int(ip[:64], 2), int(ip[64:], 2)))

def getPartitionIpv6Addr(ipv6_range, partition_index):
  """
  from a IPv6 range in the form
  {
    'addr' : addr,
    'prefixlen' : CIDR
  }
  returns the IPv6 addr
  addr::(partition_index+2) (address 1 is is used by re6st)
  If the range is too small, wrap around
  """
  addr = ipv6_range['addr']
  prefixlen = ipv6_range['prefixlen']
  prefix = binFromIpv6(addr)[:prefixlen]
  remaining = 128 - prefixlen
  suffix = bin(partition_index+2)[2:]
  if len(suffix) > remaining:
    if remaining >= 2:
      # skip reserved addresses 0 and 1
      suffix = bin((partition_index % ((1 << remaining) - 2)) + 2)[2:]
    else:
      # truncate, we have no other addresses than 0 and 1
      suffix = suffix[len(suffix) - remaining:]
  suffix = suffix.zfill(remaining)
  bits = prefix + suffix
  return dict(addr=ipv6FromBin(bits), prefixlen=prefixlen)

def getIpv6RangeFactory(k, s):
  """
  k in (1, 2, 3)
  s in ('0', '1')
  """
  def getIpv6Range(ipv6_range, partition_index, prefixshift):
    """
    from a IPv6 range in the form
    {
      'addr' : addr,
      'prefixlen' : CIDR
    }
    returns the IPv6 range
    {
      'addr' : addr:(k*(2^(prefixshift-2)) + partition_index+1)
      'prefixlen' : CIDR+prefixshift
    }
    """
    addr = ipv6_range['addr']
    prefixlen = ipv6_range['prefixlen']
    prefix = binFromIpv6(addr)[:prefixlen]
    n = prefixshift
    # we generate a subnetwork for the partition
    # the subnetwork has 16 bits more than our IPv6 range
    # make sure we have at least 2 IPs in the subnetwork
    prefixlen += n
    if prefixlen >= 128:
      raise ValueError('The IPv6 range has prefixlen {} which is too big for generating IPv6 range for partitions.'.format(prefixlen))
    return dict(
      addr=ipv6FromBin(prefix + bin((k << (n-2)) + partition_index+1)[2:].zfill(n) + s * (128 - prefixlen)),
      prefixlen=prefixlen)
  return getIpv6Range

getPartitionIpv6Range = getIpv6RangeFactory(1, '0')

getTapIpv6Range = getIpv6RangeFactory(2, '1')

getTunIpv6Range = getIpv6RangeFactory(3, '0')


def getIpv6RangeFirstAddr(addr, prefixlen):
  addr_1 = "%s1" % ipv6FromBin(binFromIpv6(addr)[:prefixlen])
  return ipv6FromBin(binFromIpv6(addr_1)) # correctly format the IPv6


def lenNetmaskIpv6(netmask):
  """Convert string represented netmask to its integer prefix"""
  # Since version 0.10.7 of netifaces, the netmask is something like "ffff::/16",
  # (it used to be "ffff::"). For old versions of netifaces, interpret the netmask
  # as an address and return its netmask, but for newer versions returns the prefixlen.
  try:
    return netaddr.IPAddress(netmask).netmask_bits()
  except ValueError:
    return netaddr.IPNetwork(netmask).prefixlen

def netmaskFromLenIPv6(netmask_len):
  """ opposite of lenNetmaskIpv6"""
  return ipv6FromBin('1' * netmask_len)

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


def rmtree(path):
  """Delete a path recursively.
  Like shutil.rmtree, but supporting the case that some files or folder
  might have been marked read only.  """
  def chmod_retry(func, failed_path, exc_info):
    """Make sure the directories are executable and writable.
    """
    # Depending on the Python version, the following items differ.
    if six.PY3:
      expected_error_type = PermissionError
      expected_func_set = {os.lstat, os.open}
    else:
      expected_error_type = OSError
      expected_func_set = {os.listdir}
    e = exc_info[1]
    if isinstance(e, expected_error_type):
      if e.errno == errno.ENOENT:
        # because we are calling again rmtree on listdir errors, this path might
        # have been already deleted by the recursive call to rmtree.
        return
      if e.errno == errno.EACCES:
        if func in expected_func_set:
          os.chmod(failed_path, 0o700)
          # corner case to handle errors in listing directories.
          # https://bugs.python.org/issue8523
          return shutil.rmtree(failed_path, onerror=chmod_retry)
        # If parent directory is not writable, we still cannot delete the file.
        # But make sure not to change the parent of the folder we are deleting.
        if failed_path != path:
          os.chmod(os.path.dirname(failed_path), 0o700)
          return func(failed_path)
    raise e  # XXX make pylint happy

  shutil.rmtree(path, onerror=chmod_retry)



class _RefResolver(jsonschema.validators.RefResolver):
  @classmethod
  def from_schema(cls, schema, read_as_json):
    instance = super(_RefResolver, cls).from_schema(schema)
    instance._read_as_json = read_as_json
    return instance

  def resolve_remote(self, uri):
    result = self._read_as_json(uri)
    if self.cache_remote:
      self.store[uri] = result
    return result


class SoftwareReleaseSerialisation(str, enum.Enum):
  Xml = 'xml'
  JsonInXml = 'json-in-xml'


class SoftwareReleaseSchemaValidationError(ValueError):
  """Error raised when a request is made with invalid parameters.

  This collects all the json schema validation errors.
  """
  def __init__(self, validation_errors):
    # type: (List[jsonschema.ValidationError]) -> None
    self.validation_errors = validation_errors
    super(SoftwareReleaseSchemaValidationError, self).__init__()

  def format_error(self, indent=0):
    def _iter_validation_error(err):
      # type: (jsonschema.ValidationError) -> Iterator[jsonschema.ValidationError]
      if err.context:
        for e in err.context:
          yield e
          # BBB PY3
          # yield from _iter_validation_error(e)
          for sube in _iter_validation_error(e):
            yield sube

    msg_list = []
    for e in self.validation_errors:
      if six.PY2:  # BBB
        def json_path(e):
          path = "$"
          for elem in e.absolute_path:
              if isinstance(elem, int):
                  path += "[" + str(elem) + "]"
              else:
                  path += "." + elem
          return path
        msg_list.append("{e_json_path}: {e.message}".format(e=e, e_json_path=json_path(e)))
      else:
        msg_list.append("{e.json_path}: {e.message}".format(e=e))

    indent_str = "\n" + (" " * indent)
    return (" " * indent) + indent_str.join(msg_list)


class SoftwareReleaseSchema(object):

  def __init__(self, software_url, software_type, download=None):
    # type: (str, Optional[str], Optional[zc.buildout.download.Download]) ->  None
    self.software_url = software_url
    # XXX: Transition from OLD_DEFAULT_SOFTWARE_TYPE ("RootSoftwareInstance")
    #      to DEFAULT_SOFTWARE_TYPE ("default") is already complete for SR schemas.
    from slapos.slap.slap import OLD_DEFAULT_SOFTWARE_TYPE, DEFAULT_SOFTWARE_TYPE
    if software_type == OLD_DEFAULT_SOFTWARE_TYPE:
      software_type = None
    self.software_type = software_type or DEFAULT_SOFTWARE_TYPE
    if download is None:
      logger = logging.getLogger(
        '{__name__}.{self.__class__.__name__}.download'.format(
          __name__=__name__, self=self))
      # zc.buildout.download logs in level info "Downloading from <URL>", which is
      # fine for normal buildout usage, but when downloading software release schemas
      # we want these messages to be logged with level debug
      logger.info = logger.debug  # type: ignore
      download = zc.buildout.download.Download(logger=logger)
    self._download = download.download

  def _warn(self, message, e):
    warnings.warn(
      "%s for software type %r of software release %s (%s: %s)"
      % (message, self.software_type, self.software_url, type(e).__name__, e),
      stacklevel=2)

  def _readAsJson(self, url, set_schema_id=False):
    # type: (str, bool) -> Optional[Dict]
    """Reads and parse the json file located at `url`.

    `url` can also be the path of a local file.
    """
    try:
      if url.startswith('http://') or url.startswith('https://'):
        path, is_temp = self._download(url)
        try:
          with open(path) as f:
            r = json.load(f)
        finally:
          if is_temp:
            os.remove(path)
      else:
        # XXX: https://discuss.python.org/t/file-uris-in-python/15600
        if url.startswith('file://'):
          path = url[7:]
        else:
          path = url
          url = 'file:' + url
        with open(path) as f:
          r = json.load(f)
      if set_schema_id and r:
        r.setdefault('$id', url)
      return r
    except Exception as e:
      warnings.warn("Unable to load JSON %s (%s: %s)"
                    % (url, type(e).__name__, e))

  def getSoftwareSchema(self):
    # type: () -> Optional[Dict]
    """Returns the schema for this software.
    """
    try:
      return self._software_schema
    except AttributeError:
      schema = self._software_schema = self._readAsJson(self.software_url + '.json')
    return schema

  def getSoftwareTypeSchema(self):
    # type: () -> Optional[Dict]
    """Returns schema for this software type.
    """
    software_schema = self.getSoftwareSchema()
    if software_schema is not None:
      try:
        return software_schema['software-type'][self.software_type]
      except Exception as e:
        self._warn("No schema defined", e)

  def getSerialisation(self, strict=False):
    # type: (bool) -> SoftwareReleaseSerialisation
    """Returns the serialisation method used for parameters.

    If strict is False, catch exceptions and return JsonInXml.
    """
    software_schema = self.getSoftwareTypeSchema()
    if software_schema is None or 'serialisation' not in software_schema:
      software_schema = self.getSoftwareSchema()
    try:
      return SoftwareReleaseSerialisation(software_schema['serialisation'])
    except Exception as e:
      if software_schema is not None: # else there was already a warning
        self._warn("Invalid or undefined serialisation", e)
      if strict:
        raise
    return SoftwareReleaseSerialisation.JsonInXml

  def getInstanceRequestParameterSchemaURL(self):
    # type: () -> Optional[str]
    """Returns the URL of the schema defining instance parameters.
    """
    software_type_schema = self.getSoftwareTypeSchema()
    if software_type_schema is None:
      return None
    return urljoin(self.software_url, software_type_schema['request'])

  def getInstanceRequestParameterSchema(self):
    # type: () -> Optional[Dict]
    """Returns the schema defining instance parameters.
    """
    try:
      return self._request_schema
    except AttributeError:
      url = self.getInstanceRequestParameterSchemaURL()
      schema = None if url is None else self._readAsJson(url, True)
      self._request_schema = schema
    return schema

  def getInstanceConnectionParameterSchemaURL(self):
    # type: () -> Optional[str]
    """Returns the URL of the schema defining connection parameters published by the instance.
    """
    software_type_schema = self.getSoftwareTypeSchema()
    if software_type_schema is None:
      return None
    return urljoin(self.software_url, software_type_schema['response'])

  def getInstanceConnectionParameterSchema(self):
    # type: () -> Optional[Dict]
    """Returns the schema defining connection parameters published by the instance.
    """
    try:
      return self._response_schema
    except AttributeError:
      url = self.getInstanceConnectionParameterSchemaURL()
      schema = None if url is None else self._readAsJson(url, True)
      self._response_schema = schema
    return schema

  def validateInstanceParameterDict(self, parameter_dict):
    # type: (Dict) -> None
    """Validate instance parameters against the software schema.

    Raise SoftwareReleaseSchemaValidationError if parameters do not
    validate.
    """
    schema = self.getInstanceRequestParameterSchema()
    if schema:
      if self.getSerialisation(strict=True) == SoftwareReleaseSerialisation.JsonInXml:
        try:
          parameter_dict = json.loads(parameter_dict['_'])
        except KeyError:
          pass
      parameter_dict.pop('$schema', None)

      validator = jsonschema.validators.validator_for(schema)(
        schema,
        resolver=_RefResolver.from_schema(schema, self._readAsJson),
      )
      errors = list(validator.iter_errors(parameter_dict))
      if errors:
        raise SoftwareReleaseSchemaValidationError(errors)


# BBB on python3 we can use pprint.pformat
class StrPrettyPrinter(pprint.PrettyPrinter):
  """A PrettyPrinter which produces consistent output on python 2 and 3
  """
  def format(self, object, context, maxlevels, level):
    if six.PY2 and isinstance(object, six.text_type):
      object = object.encode('utf-8')
    return pprint.PrettyPrinter.format(self, object, context, maxlevels, level)
