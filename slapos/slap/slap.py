# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2010 Vifib SARL and Contributors. All Rights Reserved.
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
__all__ = ["slap", "ComputerPartition", "Computer", "SoftwareRelease",
           "Supply", "OpenOrder", "NotFoundError", "Unauthorized",
           "ResourceNotReady"]

from interface import slap as interface

import httplib
try:
  import json
except ImportError:
  import simplejson as json

import socket
import ssl
import urllib
import urlparse
import zope.interface

"""
Simple, easy to (un)marshall classes for slap client/server communication
"""

# httplib.HTTPSConnection with key verification
class HTTPSConnectionCA(httplib.HTTPSConnection):
  """Patched version of HTTPSConnection which verifies server certificate"""
  def __init__(self, *args, **kwargs):
    self.ca_file = kwargs.pop('ca_file')
    if self.ca_file is None:
      raise ValueError('ca_file is required argument.')
    httplib.HTTPSConnection.__init__(self, *args, **kwargs)

  def connect(self):
    "Connect to a host on a given (SSL) port and verify its certificate."

    sock = socket.create_connection((self.host, self.port),
                                    self.timeout, self.source_address)
    if self._tunnel_host:
      self.sock = sock
      self._tunnel()
    self.sock = ssl.wrap_socket(sock, self.key_file, self.cert_file,
        ca_certs=self.ca_file, cert_reqs=ssl.CERT_REQUIRED)


def partitiondict2partition(partition_dict):
  slap_partition = ComputerPartition(partition_dict['computer_id'],
      partition_dict['computer_partition_id'])
  slap_partition._requested_state = partition_dict['requested_state']
  slap_partition._need_modification = partition_dict['need_modification']
  slap_partition._parameter_dict = partition_dict['parameter_dict']
  slap_partition._connection_dict = partition_dict['connection_dict']
  slap_partition._software_release_document = SoftwareRelease(
      software_release=partition_dict['software_release'],
      computer_guid=partition_dict['computer_id'])
  return slap_partition

class SlapDocument:
  pass

class SoftwareRelease(SlapDocument):
  """
  Contains Software Release information
  """

  zope.interface.implements(interface.ISoftwareRelease)

  def __init__(self, software_release=None, computer_guid=None, **kw):
    """
    Makes easy initialisation of class parameters

    XXX **kw args only kept for compatibility
    """
    self._software_instance_list = []
    if software_release is not None:
      software_release = software_release.encode('UTF-8')
    self._software_release = software_release
    self._computer_guid = computer_guid

  def __getinitargs__(self):
    return (self._software_release, self._computer_guid, )

  def error(self, error_log):
    # Does not follow interface
    url = '%s/software/error' % self._computer_guid,
    self._connection_helper.POST(url, {
      'url': self._software_release,
      'error_log': error_log})

  def getURI(self):
    return self._software_release

  def available(self):
    url = '%s/software/available' % self._computer_guid
    self._connection_helper.POST(url, {
      'url': self._software_release})

  def building(self):
    url = '%s/software/building' % self._computer_guid
    self._connection_helper.POST(url, {
      'url': self._software_release})

"""Exposed exceptions"""
# XXX Why do we need to expose exceptions?
class ResourceNotReady(Exception):
  pass

class ServerError(Exception):
  pass

class NotFoundError(Exception):
  zope.interface.implements(interface.INotFoundError)

class Unauthorized(Exception):
  zope.interface.implements(interface.IUnauthorized)

class Supply(SlapDocument):

  zope.interface.implements(interface.ISupply)

  def supply(self, software_release, computer_guid=None):
    self._connection_helper.POST('/%s/software' % computer_guid, json.dumps({
      'url': software_release}), "application/json")

class OpenOrder(SlapDocument):

  zope.interface.implements(interface.IOpenOrder)

  def request(self, software_release, partition_reference,
      parameter_dict_kw=None, software_type=None):
    if parameter_dict_kw is None:
      parameter_dict_kw = {}
    request_dict = {
        'software_release': software_release,
        'partition_reference': partition_reference,
        'parameter_dict': parameter_dict_kw,
      }
    if software_type is not None:
      request_dict['software_type'] = software_type
    self._connection_helper.POST('/partition', json.dumps(request_dict),
        content_type="application/json")
    json_document = self._connection_helper.response.read()
    software_instance = json.loads(json_document)
    computer_partition = ComputerPartition(
      software_instance['slap_computer_id'].encode('UTF-8'),
      software_instance['slap_computer_partition_id'].encode('UTF-8'))
    return computer_partition

def _syncComputerInformation(func):
  """
  Synchronize computer object with server information
  """
  def decorated(self, *args, **kw):
    computer = self._connection_helper.getComputerInformation(self._computer_id)
    for key, value in computer.__dict__.items():
      if isinstance(value, unicode):
        # convert unicode to utf-8
        setattr(self, key, value.encode('utf-8'))
      else:
        setattr(self, key, value)
    return func(self, *args, **kw)
  return decorated 

class Computer(SlapDocument):

  zope.interface.implements(interface.IComputer)

  def __init__(self, computer_id):
    self._computer_id = computer_id

  def __getinitargs__(self):
    return (self._computer_id, )

  @_syncComputerInformation
  def getSoftwareReleaseList(self):
    """
    Returns the list of software release which has to be supplied by the
    computer.

    Raise an INotFoundError if computer_guid doesn't exist.
    """
    return self._software_release_list

  @_syncComputerInformation
  def getComputerPartitionList(self):
    return [x for x in self._computer_partition_list if x._need_modification]

  def reportUsage(self, computer_partition_list):
    if computer_partition_list == []:
      return
    # xxx-Cedric : do not send computer, but only a dict json-compliant.
    computer = Computer(self._computer_id)
    computer.computer_partition_usage_list = computer_partition_list
    marshalled_slap_usage = json.dumps(computer)
    self._connection_helper.POST('/useComputer', {
      'computer_id': self._computer_id,
      'use_string': marshalled_slap_usage})

  def updateConfiguration(self, xml_document):
    self._connection_helper.POST(
        '/loadComputerConfigurationFromXML', { 'xml' : xml_document })
    return self._connection_helper.response.read()

def _syncComputerPartitionInformation(func):
  """
  Synchronize computer partition object with server information
  """
  def decorated(self, *args, **kw):
    computer = self._connection_helper.getComputerInformation(self._computer_id)
    found_computer_partition = None
    for computer_partition in computer._computer_partition_list:
      if computer_partition.getId() == self.getId():
        found_computer_partition = computer_partition
        break
    if found_computer_partition is None:
      raise NotFoundError("No software release information for partition %s" %
          self.getId())
    else:
      for key, value in found_computer_partition.__dict__.items():
        if isinstance(value, unicode):
          # convert unicode to utf-8
          setattr(self, key, value.encode('utf-8'))
        if isinstance(value, dict):
          new_dict = {}
          for ink, inv in value.iteritems():
            if isinstance(inv, (list, tuple)):
              new_inv = []
              for elt in inv:
                if isinstance(elt, (list, tuple)):
                  new_inv.append([x.encode('utf-8') for x in elt])
                else:
                  new_inv.append(elt.encode('utf-8'))
              new_dict[ink.encode('utf-8')] = new_inv
            elif inv is None:
              new_dict[ink.encode('utf-8')] = None
            else:
              new_dict[ink.encode('utf-8')] = inv.encode('utf-8')
          setattr(self, key, new_dict)
        else:
          setattr(self, key, value)
    return func(self, *args, **kw)
  return decorated

class ComputerPartition(SlapDocument):

  zope.interface.implements(interface.IComputerPartition)

  def __init__(self, computer_id, partition_id):
    self._computer_id = computer_id
    self._partition_id = partition_id

  def __getinitargs__(self):
    return (self._computer_id, self._partition_id, )

  # XXX: As request is decorated with _syncComputerPartitionInformation it
  #      will raise ResourceNotReady really early -- just after requesting,
  #      and not when try to access to real partition is required.
  #      To have later raising (like in case of calling methods), the way how
  #      Computer Partition data are fetch from server shall be delayed
  @_syncComputerPartitionInformation
  def request(self, software_release, software_type, partition_reference,
              shared=False, parameter_dict_kw=None, filter_kw=None):
    if parameter_dict_kw is None:
      parameter_dict_kw = {}
    elif not isinstance(parameter_dict_kw, dict):
      raise ValueError("Unexpected type of parameter_dict_kw '%s'" % \
                       parameter_dict_kw)

    if filter_kw is None:
      filter_kw = {}
    elif not isinstance(filter_kw, dict):
      raise ValueError("Unexpected type of filter_kw '%s'" % \
                       filter_kw)

    json_parameter = json.dumps({ 'computer_id': self._computer_id,
        'computer_partition_id': self._partition_id,
        'software_release': software_release,
        'software_type': software_type,
        'partition_reference': partition_reference,
        'shared': json.dumps(shared),
        'parameter_dict': json.dumps(parameter_dict_kw),
        'filter_json': json.dumps(filter_kw),
    })
    self._connection_helper.POST('/partition', json_parameter,
        content_type = "application/json")
    json_document = self._connection_helper.response.read()
    software_instance = json.loads(json_document)
    computer_partition = ComputerPartition(
      software_instance['slap_computer_id'].encode('UTF-8'),
      software_instance['slap_computer_partition_id'].encode('UTF-8'))
    return computer_partition

  def building(self):
    url = "/%s/partition/%s/building" % (self._computer_id,
                                          self._partition_id)
    self._connection_helper.POST(url)

  def available(self):
    url = "/%s/partition/%s/available" % (self._computer_id, 
                                          self._partition_id)
    self._connection_helper.POST(url)

  def destroyed(self):
    url = "/%s/partition/%s/destroyed" % (self._computer_id, 
                                          self._partition_id)
    self._connection_helper.POST(url)

  def started(self):
    url = "/%s/partition/%s/started" % (self._computer_id,
                                          self._partition_id)
    self._connection_helper.POST(url)

  def stopped(self):
    url = "/%s/partition/%s/stopped" % (self._computer_id,
                                          self._partition_id)
    self._connection_helper.POST(url)

  def error(self, error_log):
    url = "/%s/partition/%s/error" % (self._computer_id,
                                          self._partition_id)
    self._connection_helper.POST(url, {
      'error_log': error_log, })

  def getId(self):
    return self._partition_id

  @_syncComputerPartitionInformation
  def getState(self):
    return self._requested_state

  @_syncComputerPartitionInformation
  def getInstanceParameterDict(self):
    return getattr(self, '_parameter_dict', None) or {}

  @_syncComputerPartitionInformation
  def getSoftwareRelease(self):
    """
    Returns the software release associate to the computer partition.
    """
    if self._software_release_document is None:
      raise NotFoundError("No software release information for partition %s" %
          self.getId())
    else:
      return self._software_release_document

  def setConnectionDict(self, connection_dict):
    self._connection_helper.POST('/%s/partition/%s' % (
        self._computer_id, self._partition_id), json.dumps(connection_dict), 
        'application/json')

  @_syncComputerPartitionInformation
  def getConnectionParameter(self, key):
    connection_dict = getattr(self, '_connection_dict', None) or {}
    if key in connection_dict:
      return connection_dict[key]
    else:
      raise NotFoundError("%s not found" % key)

  def setUsage(self, usage_log):
    # XXX: this implementation has not been reviewed
    self.usage = usage_log

  def getCertificate(self):
    self._connection_helper.GET(
        '/getComputerPartitionCertificate?computer_id=%s&'
        'computer_partition_id=%s' % (self._computer_id, self._partition_id))
    return json.loads(self._connection_helper.response.read())

# def lazyMethod(func):
#   """
#   Return a function which stores a computed value in an instance
#   at the first call.
#   """
#   key = '_cache_' + str(id(func))
#   def decorated(self, *args, **kw):
#     try:
#       return getattr(self, key)
#     except AttributeError:
#       result = func(self, *args, **kw)
#       setattr(self, key, result)
#       return result
#   return decorated 

class ConnectionHelper:
  error_message_connect_fail = "Couldn't connect to the server. Please double \
check given master-url argument, and make sure that IPv6 is enabled on \
your machine and that the server is available. The original error was:"
  def __init__(self, connection_wrapper, host, path, key_file=None,
      cert_file=None, master_ca_file=None):
    self.connection_wrapper = connection_wrapper
    self.host = host
    self.path = path
    self.key_file = key_file
    self.cert_file = cert_file
    self.master_ca_file = master_ca_file

  def getComputerInformation(self, computer_id):
    self.GET('/%s' % computer_id)
    dict_computer = json.loads(self.response.read())
    # Build the computer object from our dict
    # XXX-Cedric : would it be better to use dict_computer.get('couscous')?
    computer = Computer(dict_computer['computer_id'])
    computer._software_release_list = []
    for sr in dict_computer['software_release_list']:
      computer._software_release_list.append(SoftwareRelease(
          software_release=sr['software_release'],
          computer_guid=dict_computer['computer_id']))
    computer._computer_partition_list = []
    for partition in dict_computer['computer_partition_list']:
        computer._computer_partition_list.append(partitiondict2partition(
        partition))
    return computer

  def connect(self):
    connection_dict = dict(
        host=self.host)
    if self.key_file and self.cert_file:
      connection_dict.update(
        key_file=self.key_file,
        cert_file=self.cert_file)
    if self.master_ca_file is not None:
      connection_dict.update(ca_file=self.master_ca_file)
    self.connection = self.connection_wrapper(**connection_dict)

  def GET(self, path):
    try:
      self.connect()
      self.connection.request('GET', self.path + path)
      self.response = self.connection.getresponse()
    except socket.error, e:
      raise socket.error(self.error_message_connect_fail + str(e))
    # check self.response.status and raise exception early
    if self.response.status == httplib.REQUEST_TIMEOUT:
      # resource is not ready
      raise ResourceNotReady(path)
    elif self.response.status == httplib.NOT_FOUND:
      raise NotFoundError(path)
    elif self.response.status == httplib.FORBIDDEN:
      raise Unauthorized(path)
    elif self.response.status != httplib.OK:
      message = 'Server responded with wrong code %s with %s' % \
                                         (self.response.status, path)
      raise ServerError(message)

  def POST(self, path, parameter_dict,
      content_type="application/x-www-form-urlencoded"):
    # XXX-Cedric : we should change content_type to be json by default
    try:
      self.connect()
      header_dict = {'Content-type': content_type}
      if content_type != 'application/json':
        parameter_dict = urllib.urlencode(parameter_dict)
      self.connection.request("POST", self.path + path,
          parameter_dict, header_dict)
    except socket.error, e:
      raise socket.error(self.error_message_connect_fail + str(e))
    self.response = self.connection.getresponse()
    # check self.response.status and raise exception early
    if self.response.status == httplib.REQUEST_TIMEOUT:
      # resource is not ready
      raise ResourceNotReady("%s - %s" % (path, parameter_dict))
    elif self.response.status == httplib.NOT_FOUND:
      raise NotFoundError("%s - %s" % (path, parameter_dict))
    elif self.response.status == httplib.FORBIDDEN:
      raise Unauthorized("%s - %s" % (path, parameter_dict))
    elif self.response.status != httplib.OK:
      message = 'Server responded with wrong code %s with %s' % \
                                         (self.response.status, path)
      raise ServerError(message)

class slap:

  zope.interface.implements(interface.slap)

  def initializeConnection(self, slapgrid_uri, key_file=None, cert_file=None,
      master_ca_file=None):
    self._initialiseConnectionHelper(slapgrid_uri, key_file, cert_file,
        master_ca_file)

  def _initialiseConnectionHelper(self, slapgrid_uri, key_file, cert_file,
      master_ca_file):
    SlapDocument._slapgrid_uri = slapgrid_uri
    scheme, netloc, path, query, fragment = urlparse.urlsplit(
        SlapDocument._slapgrid_uri)
    if not(query == '' and fragment == ''):
      raise AttributeError('Passed URL %r issue: not parseable'%
          SlapDocument._slapgrid_uri)
    if scheme not in ('http', 'https'):
      raise AttributeError('Passed URL %r issue: there is no support for %r p'
          'rotocol' % (SlapDocument._slapgrid_uri, scheme))

    if scheme == 'http':
      connection_wrapper = httplib.HTTPConnection
    else:
      if master_ca_file is not None:
        connection_wrapper = HTTPSConnectionCA
      else:
        connection_wrapper = httplib.HTTPSConnection
    slap._connection_helper = \
      SlapDocument._connection_helper = ConnectionHelper(connection_wrapper,
          netloc, path, key_file, cert_file, master_ca_file)

  def _register(self, klass, *registration_argument_list):
    if len(registration_argument_list) == 1 and type(
        registration_argument_list[0]) == type([]):
      # in case if list is explicitly passed and there is only one
      # argument in registration convert it to list
      registration_argument_list = registration_argument_list[0]
    document = klass(*registration_argument_list)
    return document

  def registerSoftwareRelease(self, software_release):
    """
    Registers connected representation of software release and
    returns SoftwareRelease class object
    """
    return SoftwareRelease(software_release=software_release)

  def registerComputer(self, computer_guid):
    """
    Registers connected representation of computer and
    returns Computer class object
    """
    self.computer_guid = computer_guid
    return self._register(Computer, computer_guid)

  def registerComputerPartition(self, computer_guid, partition_id):
    """
    Registers connected representation of computer partition and
    returns Computer Partition class object
    """
    # XXX-Cedric : we have a problem when computer_guid or partition_id have 
    # space. Should we forbid spaces? What about special chars?
    self._connection_helper.GET('/%s/partition/%s' % (
          computer_guid, partition_id))
    json_document = self._connection_helper.response.read()
    return partitiondict2partition(json.loads(json_document))

  def registerOpenOrder(self):
    return OpenOrder()

  def registerSupply(self):
    return Supply()
