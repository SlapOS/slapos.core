# -*- coding: utf-8 -*-
# vim: set et sts=2:
##############################################################################
#
# Copyright (c) 2010, 2011, 2012 Vifib SARL and Contributors.
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
"""
Simple, easy to (un)marshall classes for slap client/server communication
"""

__all__ = ["slap", "ComputerPartition", "Computer", "SoftwareRelease",
           "SoftwareInstance", "SoftwareProductCollection",
           "Supply", "OpenOrder", "NotFoundError", "Token",
           "ResourceNotReady", "ServerError", "ConnectionError"]

import os
import logging
import re
from functools import wraps
import warnings

import json
import jsonschema
import six

from .exception import ResourceNotReady, ServerError, NotFoundError, \
          ConnectionError
from .hateoas import SlapHateoasNavigator, ConnectionHelper
from slapos.util import (SoftwareReleaseSchema, bytes2str, calculate_dict_hash,
                         dict2xml, dumps, loads, unicode2str, xml2dict)

from xml.sax import saxutils
from zope.interface import implementer
from .interface import slap as interface


import requests
# silence messages like 'Starting connection' that are logged with INFO
urllib3_logger = logging.getLogger('requests.packages.urllib3')
urllib3_logger.setLevel(logging.WARNING)


# XXX fallback_logger to be deprecated together with the old CLI entry points.
fallback_logger = logging.getLogger(__name__)
fallback_handler = logging.StreamHandler()
fallback_logger.setLevel(logging.INFO)
fallback_logger.addHandler(fallback_handler)


DEFAULT_SOFTWARE_TYPE = 'RootSoftwareInstance'
COMPUTER_PARTITION_REQUEST_LIST_TEMPLATE_FILENAME = '.slapos-request-transaction-%s'

class SlapDocument:
  def __init__(self, connection_helper=None, hateoas_navigator=None):
    if connection_helper is not None:
      # Do not require connection_helper to be provided, but when it's not,
      # cause failures when accessing _connection_helper property.
      self._connection_helper = connection_helper
      self._hateoas_navigator = hateoas_navigator


class SlapRequester(SlapDocument):
  """
  Abstract class that allow to factor method for subclasses that use "request()"
  """

  def _requestComputerPartition(self, request_dict):

    try:
      SoftwareReleaseSchema(
          request_dict['software_release'],
          request_dict['software_type']
      ).validateInstanceParameterDict(
          loads(request_dict['partition_parameter_xml']))
    except jsonschema.ValidationError as e:
      warnings.warn(
        "Request parameters do not validate against schema definition:\n{e}".format(e=e),
        UserWarning,
      )
    except Exception as e:
      # note that we intentionally catch wide exceptions, so that if anything
      # is wrong with fetching the schema or the schema itself this does not
      # prevent users from requesting instances.
      warnings.warn(
        "Error validating request parameters against schema definition:\n{e.__class__.__name__} {e}".format(e=e),
        UserWarning,
      )

    try:
      xml = self._connection_helper.POST('requestComputerPartition', data=request_dict)
    except ResourceNotReady:
      return ComputerPartition(
        request_dict=request_dict,
        connection_helper=self._connection_helper,
      )
    software_instance = loads(xml)
    computer_partition = ComputerPartition(
      software_instance.slap_computer_id,
      software_instance.slap_computer_partition_id,
      connection_helper=self._connection_helper,
    )
    # Hack to give all object attributes to the ComputerPartition instance
    # XXX Should be removed by correctly specifying difference between
    # ComputerPartition and SoftwareInstance
    computer_partition.__dict__.update(software_instance.__dict__)
    # XXX not generic enough.
    if loads(request_dict['shared_xml']):
      computer_partition._synced = True
      computer_partition._connection_dict = software_instance._connection_dict
      computer_partition._parameter_dict = software_instance._parameter_dict
    return computer_partition


@implementer(interface.ISoftwareRelease)
class SoftwareRelease(SlapDocument):
  """
  Contains Software Release information
  """

  def __init__(self, software_release=None, computer_guid=None, requested_state='available', **kw):
    """
    Makes easy initialisation of class parameters

    XXX **kw args only kept for compatibility
    """
    SlapDocument.__init__(self, kw.pop('connection_helper', None),
                                kw.pop('hateoas_navigator', None))
    self._software_instance_list = []
    self._software_release = software_release
    self._computer_guid = computer_guid

  def __getinitargs__(self):
    return (self._software_release, self._computer_guid, )

  def getComputerId(self):
    if not self._computer_guid:
      raise NameError('computer_guid has not been defined.')
    else:
      return self._computer_guid

  def getURI(self):
    if not self._software_release:
      raise NameError('software_release has not been defined.')
    else:
      return self._software_release

  def error(self, error_log, logger=None):
    try:
      # Does not follow interface
      self._connection_helper.POST('softwareReleaseError', data={
        'url': self.getURI(),
        'computer_id': self.getComputerId(),
        'error_log': error_log})
    except Exception:
      (logger or fallback_logger).exception('')

  def available(self):
    if getattr(self, '_known_state', 'unknown') != "available":
      # Not required to repost if not needed.
      self._connection_helper.POST('availableSoftwareRelease', data={
        'url': self.getURI(),
        'computer_id': self.getComputerId()})

  def building(self):
    if getattr(self, '_known_state', 'unknown') != "building":
      self._connection_helper.POST('buildingSoftwareRelease', data={
        'url': self.getURI(),
        'computer_id': self.getComputerId()})

  def destroyed(self):
    self._connection_helper.POST('destroyedSoftwareRelease', data={
      'url': self.getURI(),
      'computer_id': self.getComputerId()})

  def getState(self):
    return getattr(self, '_requested_state', 'available')


@implementer(interface.ISoftwareProductCollection)
class SoftwareProductCollection(object):

  def __init__(self, logger, slap):
    self.logger = logger
    self.slap = slap
    self.get = self.__getattr__

  def __getattr__(self, software_product):
      self.logger.info('Getting best Software Release corresponding to '
                       'this Software Product...')
      software_release_list = \
          self.slap.getSoftwareReleaseListFromSoftwareProduct(software_product)
      try:
          software_release_url = software_release_list[0] # First is best one.
          self.logger.info('Found as %s.' % software_release_url)
          return software_release_url
      except IndexError:
          raise AttributeError('No Software Release corresponding to this '
                           'Software Product has been found.')


# XXX What is this SoftwareInstance class?
@implementer(interface.ISoftwareInstance)
class SoftwareInstance(SlapDocument):
  """
  Contains Software Instance information
  """

  def __init__(self, **kw):
    """
    Makes easy initialisation of class parameters
    """
    self.__dict__.update(kw)



@implementer(interface.ISupply)
class Supply(SlapDocument):

  def supply(self, software_release, computer_guid=None, state='available'):
    try:
      self._connection_helper.POST('supplySupply', data={
        'url': software_release,
        'computer_id': computer_guid,
        'state': state})
    except NotFoundError:
      raise NotFoundError("Computer %s has not been found by SlapOS Master."
          % computer_guid)

@implementer(interface.IToken)
class Token(SlapDocument):
  def request(self):
    return self._hateoas_navigator.getToken()

@implementer(interface.IOpenOrder)
class OpenOrder(SlapRequester):

  def request(self, software_release, partition_reference,
              partition_parameter_kw=None, software_type=None,
              filter_kw=None, state=None, shared=False):

    if partition_parameter_kw is None:
      partition_parameter_kw = {}
    elif not isinstance(partition_parameter_kw, dict):
      raise ValueError("Unexpected type of partition_parameter_kw '%s'" %
                       partition_parameter_kw)

    if filter_kw is None:
      filter_kw = {}
    elif not isinstance(filter_kw, dict):
      raise ValueError("Unexpected type of filter_kw '%s'" %
                       filter_kw)

    # Let enforce a default software type
    if software_type is None:
      software_type = DEFAULT_SOFTWARE_TYPE

    request_dict = {
        'software_release': software_release,
        'partition_reference': partition_reference,
        'partition_parameter_xml': dumps(partition_parameter_kw),
        'filter_xml': dumps(filter_kw),
        'software_type': software_type,
        # XXX Cedric: Why state and shared are marshalled? First is a string
        #             And second is a boolean.
        'state': dumps(state),
        'shared_xml': dumps(shared),
    }
    return self._requestComputerPartition(request_dict)

  def getInformation(self, partition_reference):
    if not getattr(self, '_hateoas_navigator', None):
      raise Exception('SlapOS Master Hateoas API required for this operation is not available.')
    raw_information = self._hateoas_navigator.getInstanceTreeRootSoftwareInstanceInformation(partition_reference)
    software_instance = SoftwareInstance()
    # XXX redefine SoftwareInstance to be more consistent
    for key, value in six.iteritems(raw_information["data"]):
      if key in ['_links']:
        continue
      setattr(software_instance, '_%s' % key, value)

    if raw_information["data"].get("text_content", None) is not None:
      result_dict = xml2dict(unicode2str(raw_information["data"]['text_content']))
      # the '_' parameter contains a stringified JSON which is not easily readable by human
      # we parse it as a dict so that it is displayed in the console as a dict (beautiful display on several lines)
      if len(result_dict) == 1 and '_' in result_dict:
        result_dict['_'] = json.loads(result_dict['_'])
      software_instance._parameter_dict = result_dict
    else:
      software_instance._parameter_dict = {}

    software_instance._requested_state = raw_information["data"]['slap_state']
    software_instance._connection_dict = raw_information["data"]['connection_parameter_list']
    software_instance._software_release_url = raw_information["data"]['url_string']
    return software_instance

  def requestComputer(self, computer_reference):
    """
    Requests a computer.
    """
    xml = self._connection_helper.POST('requestComputer', data={'computer_title': computer_reference})
    computer = loads(xml)
    computer._connection_helper = self._connection_helper
    computer._hateoas_navigator = self._hateoas_navigator
    return computer


def _syncComputerInformation(func):
  """
  Synchronize computer object with server information
  """
  def decorated(self, *args, **kw):
    if not getattr(self, '_synced', 0):
      computer = self._connection_helper.getFullComputerInformation(
        self._computer_id)
      self.__dict__.update(computer.__dict__)
      self._synced = True
      for computer_partition in self.getComputerPartitionList():
        computer_partition._synced = True
    return func(self, *args, **kw)
  return wraps(func)(decorated)


@implementer(interface.IComputer)
class Computer(SlapDocument):

  def __init__(self, computer_id, connection_helper=None, hateoas_navigator=None):
    SlapDocument.__init__(self, connection_helper, hateoas_navigator)
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
    for software_relase in self._software_release_list:
      software_relase._connection_helper = self._connection_helper
      software_relase._hateoas_navigator = self._hateoas_navigator
    return self._software_release_list

  @_syncComputerInformation
  def getComputerPartitionList(self):
    for computer_partition in self._computer_partition_list:
      computer_partition._connection_helper = self._connection_helper
      computer_partition._hateoas_navigator = self._hateoas_navigator
    return [x for x in self._computer_partition_list]

  def reportUsage(self, computer_usage):
    if computer_usage == "":
      return
    self._connection_helper.POST('useComputer', data={
      'computer_id': self._computer_id,
      'use_string': computer_usage})

  def updateConfiguration(self, xml):
    return self._connection_helper.POST('loadComputerConfigurationFromXML', data={'xml': xml})

  def bang(self, message):
    self._connection_helper.POST('computerBang', data={
      'computer_id': self._computer_id,
      'message': message})

  def getStatus(self):
    xml = self._connection_helper.GET('getComputerStatus', params={'computer_id': self._computer_id})
    return loads(xml)

  def revokeCertificate(self):
    self._connection_helper.POST('revokeComputerCertificate', data={
      'computer_id': self._computer_id})

  def generateCertificate(self):
    xml = self._connection_helper.POST('generateComputerCertificate', data={
      'computer_id': self._computer_id})
    return loads(xml)

  def getInformation(self):
    if not getattr(self, '_hateoas_navigator', None):
      raise Exception('SlapOS Master Hateoas API required for this operation is not available.')
    raw_information = self._hateoas_navigator._getComputer(reference=self._computer_id)
    computer = Computer(self._computer_id) 
    for key, value in six.iteritems(raw_information["data"]):
      if key in ['_links']:
        continue
      setattr(computer, '_%s' % key, value)
    return computer


def parsed_error_message(status, body, path):
  m = re.search('(Error Value:\n.*)', body, re.MULTILINE)
  if m:
    match = ' '.join(line.strip() for line in m.group(0).split('\n'))
    return '%s (status %s while calling %s)' % (
                saxutils.unescape(match),
                status,
                path
            )
  else:
    return 'Server responded with wrong code %s with %s' % (status, path)


@implementer(interface.IComputerPartition)
class ComputerPartition(SlapRequester):

  def __init__(self, computer_id=None, partition_id=None,
               request_dict=None, connection_helper=None,
               hateoas_navigator=None):
    SlapDocument.__init__(self, connection_helper, hateoas_navigator)
    if request_dict is not None and (computer_id is not None or
        partition_id is not None):
      raise TypeError('request_dict conflicts with computer_id and '
        'partition_id')
    if request_dict is None and (computer_id is None or partition_id is None):
      raise TypeError('computer_id and partition_id or request_dict are '
        'required')
    self._computer_id = computer_id
    self._partition_id = partition_id
    self._request_dict = request_dict

    # Just create an empty file (for nothing requested yet)
    self._updateTransactionFile(partition_reference=None)

  def __getinitargs__(self):
    return (self._computer_id, self._partition_id, )

  def _updateTransactionFile(self, partition_reference=None):
    """
    Store reference to all Instances requested by this Computer Parition
    """
    # Environ variable set by Slapgrid while processing this partition
    instance_root = os.environ.get('SLAPGRID_INSTANCE_ROOT', '')
    if not instance_root or not self._partition_id:
      return

    transaction_file_name = COMPUTER_PARTITION_REQUEST_LIST_TEMPLATE_FILENAME % self._partition_id
    transaction_file_path = os.path.join(instance_root, self._partition_id,
                                        transaction_file_name)

    try:
      if partition_reference is None:
        if os.access(os.path.join(instance_root, self._partition_id), os.W_OK):
          if os.path.exists(transaction_file_path):
            return
          transac_file = open(transaction_file_path, 'w')
          transac_file.close()
      else:
        with open(transaction_file_path, 'a') as transac_file:
          transac_file.write('%s\n' % partition_reference)
    except OSError:
      return

  def request(self, software_release, software_type, partition_reference,
              shared=False, partition_parameter_kw=None, filter_kw=None,
              state=None):
    if partition_parameter_kw is None:
      partition_parameter_kw = {}
    elif not isinstance(partition_parameter_kw, dict):
      raise ValueError("Unexpected type of partition_parameter_kw '%s'" %
                       partition_parameter_kw)

    if filter_kw is None:
      filter_kw = {}
    elif not isinstance(filter_kw, dict):
      raise ValueError("Unexpected type of filter_kw '%s'" %
                       filter_kw)

    # Let enforce a default software type
    if software_type is None:
      software_type = DEFAULT_SOFTWARE_TYPE

    request_dict = {
        'computer_id': self._computer_id,
        'computer_partition_id': self._partition_id,
        'software_release': software_release,
        'software_type': software_type,
        'partition_reference': partition_reference,
        'shared_xml': dumps(shared),
        'partition_parameter_xml': dumps(partition_parameter_kw),
        'filter_xml': dumps(filter_kw),
        'state': dumps(state),
    }
    self._updateTransactionFile(partition_reference)
    return self._requestComputerPartition(request_dict)

  def destroyed(self):
    self._connection_helper.POST('destroyedComputerPartition', data={
      'computer_id': self._computer_id,
      'computer_partition_id': self.getId(),
      })

  def started(self):
    self._connection_helper.POST('startedComputerPartition', data={
      'computer_id': self._computer_id,
      'computer_partition_id': self.getId(),
      })

  def stopped(self):
    self._connection_helper.POST('stoppedComputerPartition', data={
      'computer_id': self._computer_id,
      'computer_partition_id': self.getId(),
      })

  def error(self, error_log, logger=None):
    try:
      self._connection_helper.POST('softwareInstanceError', data={
        'computer_id': self._computer_id,
        'computer_partition_id': self.getId(),
        'error_log': error_log})
    except Exception:
      (logger or fallback_logger).exception('')

  def bang(self, message):
    self._connection_helper.POST('softwareInstanceBang', data={
      'computer_id': self._computer_id,
      'computer_partition_id': self.getId(),
      'message': message})

  def rename(self, new_name, slave_reference=None):
    post_dict = {
            'computer_id': self._computer_id,
            'computer_partition_id': self.getId(),
            'new_name': new_name,
            }
    if slave_reference:
      post_dict['slave_reference'] = slave_reference
    self._connection_helper.POST('softwareInstanceRename', data=post_dict)

  def getInformation(self, partition_reference):
    """
    Return all needed informations about an existing Computer Partition
    in the Instance tree of the current Computer Partition.
    """
    if not getattr(self, '_hateoas_navigator', None):
      raise Exception('SlapOS Master Hateoas API required for this operation is not available.')

    instance_url = self.getMeUrl()
    raw_information = self._hateoas_navigator.getRelatedInstanceInformation(
      instance_url, partition_reference)
    software_instance = SoftwareInstance()
    for key, value in six.iteritems(raw_information["data"]):
      if key in ['_links']:
        continue
      setattr(software_instance, '_%s' % key, value)

    if raw_information["data"].get("text_content", None) is not None:
      setattr(software_instance, '_parameter_dict', xml2dict(raw_information["data"]['text_content']))
    else:
      setattr(software_instance, '_parameter_dict', {})

    setattr(software_instance, '_requested_state', raw_information["data"]['slap_state'])
    setattr(software_instance, '_connection_dict', raw_information["data"]['connection_parameter_list'])
    setattr(software_instance, '_software_release_url', raw_information["data"]['url_string'])
    return software_instance

  def getId(self):
    if not getattr(self, '_partition_id', None):
      raise ResourceNotReady()
    return self._partition_id

  def getInstanceGuid(self):
    """Return instance_guid. Raise ResourceNotReady if it doesn't exist."""
    if not getattr(self, '_instance_guid', None):
      raise ResourceNotReady()
    return self._instance_guid

  def getState(self):
    """return _requested_state. Raise ResourceNotReady if it doesn't exist."""
    if not getattr(self, '_requested_state', None):
      raise ResourceNotReady()
    return self._requested_state

  def getAccessStatus(self):
    """Get latest computer partition Access message state"""
    return getattr(self, '_access_status', None)

  def getType(self):
    """
    return the Software Type of the instance.
    Raise RessourceNotReady if not present.
    """
    # XXX: software type should not belong to the parameter dict.
    software_type = self.getInstanceParameterDict().get(
        'slap_software_type', None)
    if not software_type:
      raise ResourceNotReady()
    return software_type

  def getInstanceParameterDict(self):
    return getattr(self, '_parameter_dict', None) or {}

  def getConnectionParameterDict(self):
    connection_dict = getattr(self, '_connection_dict', None)
    if connection_dict is None:
      # XXX Backward compatibility for older slapproxy (<= 1.0.0)
      connection_dict = xml2dict(getattr(self, 'connection_xml', ''))

    return connection_dict or {}

  def getSoftwareRelease(self):
    """
    Returns the software release associate to the computer partition.
    """
    if not getattr(self, '_software_release_document', None):
      raise NotFoundError("No software release information for partition %s" %
          self.getId())
    else:
      return self._software_release_document

  def setConnectionDict(self, connection_dict, slave_reference=None):
    # recreate and stabilise connection_dict that it would became the same as on server
    connection_dict = xml2dict(dict2xml(connection_dict))
    if self.getConnectionParameterDict() == connection_dict:
      return

    if slave_reference is not None:
      # check the connection parameters from the slave

      # Should we check existence?
      slave_parameter_list = self.getInstanceParameter("slave_instance_list")
      slave_connection_dict = {}
      connection_parameter_hash = None
      for slave_parameter_dict in slave_parameter_list:
        if slave_parameter_dict.get("slave_reference") == slave_reference:
          connection_parameter_hash = slave_parameter_dict.get("connection-parameter-hash", None)
          break

      # Skip as nothing changed for the slave
      if connection_parameter_hash is not None and \
        connection_parameter_hash == calculate_dict_hash(connection_dict):
        return

    self._connection_helper.POST('setComputerPartitionConnectionXml', data={
          'computer_id': self._computer_id,
          'computer_partition_id': self._partition_id,
          'connection_xml': dumps(connection_dict),
          'slave_reference': slave_reference})

  def getInstanceParameter(self, key):
    parameter_dict = getattr(self, '_parameter_dict', None) or {}
    try:
      return parameter_dict[key]
    except KeyError:
      raise NotFoundError("%s not found" % key)

  def getConnectionParameter(self, key):
    connection_dict = self.getConnectionParameterDict()
    try:
      return connection_dict[key]
    except KeyError:
      raise NotFoundError("%s not found" % key)

  def setUsage(self, usage_log):
    # XXX: this implementation has not been reviewed
    self.usage = usage_log

  def getCertificate(self):
    xml = self._connection_helper.GET('getComputerPartitionCertificate',
            params={
                'computer_id': self._computer_id,
                'computer_partition_id': self._partition_id,
                }
            )
    return loads(xml)

  def getStatus(self):
    xml = self._connection_helper.GET('getComputerPartitionStatus',
            params={
                'computer_id': self._computer_id,
                'computer_partition_id': self._partition_id,
                }
            )
    return loads(xml)
  
  def getFullHostingIpAddressList(self):
    xml = self._connection_helper.GET('getHostingSubscriptionIpList',
            params={
                'computer_id': self._computer_id,
                'computer_partition_id': self._partition_id,
                }
            )
    return loads(xml)

  def setComputerPartitionRelatedInstanceList(self, instance_reference_list):
    self._connection_helper.POST('updateComputerPartitionRelatedInstanceList',
        data={
          'computer_id': self._computer_id,
          'computer_partition_id': self._partition_id,
          'instance_reference_xml': dumps(instance_reference_list)
          }
        )

class SlapConnectionHelper(ConnectionHelper):

  def getComputerInformation(self, computer_id):
    xml = self.GET('getComputerInformation', params={'computer_id': computer_id})
    return loads(xml)

  def getFullComputerInformation(self, computer_id):
    """
    Retrieve from SlapOS Master Computer instance containing all needed
    informations (Software Releases, Computer Partitions, ...).
    """
    path = 'getFullComputerInformation'
    params = {'computer_id': computer_id}
    if not computer_id:
      # XXX-Cedric: should raise something smarter than "NotFound".
      raise NotFoundError('%r %r' % (path, params))
    try:
      xml = self.GET(path, params=params)
    except NotFoundError:
      # XXX: This is a ugly way to keep backward compatibility,
      # We should stablise slap library soon.
      xml = self.GET('getComputerInformation', params=params)

    return loads(xml)

getHateoasUrl_cache = {}
@implementer(interface.slap)
class slap:

  def initializeConnection(self, slapgrid_uri,
                           key_file=None, cert_file=None,
                           master_ca_file=None,
                           timeout=60,
                           slapgrid_rest_uri=None):
    if master_ca_file:
      raise NotImplementedError('Master certificate not verified in this version: %s' % master_ca_file)

    self._connection_helper = SlapConnectionHelper(
            slapgrid_uri, key_file, cert_file, master_ca_file, timeout)

    if not slapgrid_rest_uri:
      getHateoasUrl_cache_key = (slapgrid_uri, key_file, cert_file, master_ca_file, timeout)
      try:
        slapgrid_rest_uri = getHateoasUrl_cache[getHateoasUrl_cache_key]
      except KeyError:
        pass
    if not slapgrid_rest_uri:
      try:
        slapgrid_rest_uri = getHateoasUrl_cache[getHateoasUrl_cache_key] = \
          bytes2str(self._connection_helper.GET('getHateoasUrl'))
      except:
        pass
    if slapgrid_rest_uri:
      self._hateoas_navigator = SlapHateoasNavigator(
          slapgrid_rest_uri,
          key_file, cert_file,
          master_ca_file, timeout
      )
    else:
      self._hateoas_navigator = None

  # XXX-Cedric: this method is never used and thus should be removed.
  def registerSoftwareRelease(self, software_release):
    """
    Registers connected representation of software release and
    returns SoftwareRelease class object
    """
    return SoftwareRelease(software_release=software_release,
      connection_helper=self._connection_helper,
      hateoas_navigator=self._hateoas_navigator
    )

  def registerToken(self):
    """
    Registers connected represenation of token and
    return Token class object
    """
    if not getattr(self, '_hateoas_navigator', None):
      raise Exception('SlapOS Master Hateoas API required for this operation is not available.')

    return Token(
      connection_helper=self._connection_helper,
      hateoas_navigator=self._hateoas_navigator
    )


  def registerComputer(self, computer_guid):
    """
    Registers connected representation of computer and
    returns Computer class object
    """
    return Computer(computer_guid,
      connection_helper=self._connection_helper,
      hateoas_navigator=self._hateoas_navigator
    )

  def registerComputerPartition(self, computer_guid, partition_id):
    """
    Registers connected representation of computer partition and
    returns Computer Partition class object
    """
    if not computer_guid or not partition_id:
      # XXX-Cedric: should raise something smarter than NotFound
      raise NotFoundError

    xml = self._connection_helper.GET('registerComputerPartition',
            params = {
                'computer_reference': computer_guid,
                'computer_partition_reference': partition_id,
                }
            )
    result = loads(xml)
    # XXX: dirty hack to make computer partition usable. xml_marshaller is too
    # low-level for our needs here.
    result._connection_helper = self._connection_helper
    result._hateoas_navigator = self._hateoas_navigator
    return result

  def registerOpenOrder(self):
    return OpenOrder(
      connection_helper=self._connection_helper,
      hateoas_navigator=self._hateoas_navigator
  )

  def registerSupply(self):
    return Supply(
      connection_helper=self._connection_helper,
      hateoas_navigator=self._hateoas_navigator
  )

  def getSoftwareReleaseListFromSoftwareProduct(self,
      software_product_reference=None, software_release_url=None):
    url = 'getSoftwareReleaseListFromSoftwareProduct'
    params = {}
    if software_product_reference:
      if software_release_url is not None:
        raise AttributeError('Both software_product_reference and '
                             'software_release_url parameters are specified.')
      params['software_product_reference'] = software_product_reference
    else:
      if software_release_url is None:
        raise AttributeError('None of software_product_reference and '
                             'software_release_url parameters are specified.')
      params['software_release_url'] = software_release_url

    xml = self._connection_helper.GET(url, params=params)
    result = loads(xml)
    assert(type(result) == list)
    return result

  def getOpenOrderDict(self):
    if not getattr(self, '_hateoas_navigator', None):
      raise Exception('SlapOS Master Hateoas API required for this operation is not available.')
    return self._hateoas_navigator.getInstanceTreeDict()

  def getComputerDict(self): 
    if not getattr(self, '_hateoas_navigator', None):
      raise Exception('SlapOS Master Hateoas API required for this operation is not available.')
    return self._hateoas_navigator.getComputerDict()

