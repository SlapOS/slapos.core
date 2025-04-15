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

import json
import six

try:
  from typing import Mapping, Sequence
except ImportError: # XXX to be removed once we depend on typing
  pass

from .exception import ResourceNotReady, ServerError, NotFoundError, \
          ConnectionError
from .hateoas import SlapHateoasNavigator, ConnectionHelper
from slapos.util import (bytes2str, dict2xml, dumps, loads,
                         unicode2str, xml2dict)

from xml.sax import saxutils
from zope.interface import implementer
from .interface import slap as interface


import requests
from requests.exceptions import RequestException

# silence messages like 'Starting connection' that are logged with INFO
urllib3_logger = logging.getLogger('requests.packages.urllib3')
urllib3_logger.setLevel(logging.WARNING)


# XXX fallback_logger to be deprecated together with the old CLI entry points.
fallback_logger = logging.getLogger(__name__)
fallback_handler = logging.StreamHandler()
fallback_logger.setLevel(logging.INFO)
fallback_logger.addHandler(fallback_handler)


OLD_DEFAULT_SOFTWARE_TYPE = 'RootSoftwareInstance'
DEFAULT_SOFTWARE_TYPE = 'default'
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
    result = self._connection_helper.callJsonRpcAPI(
      'slapos.post.software_instance',
      {
        'title': request_dict['partition_reference'],
        'software_release_uri': request_dict['software_release'],
        'software_type': request_dict['software_type'],
        'state': loads(request_dict['state']),
        'parameters': loads(request_dict['partition_parameter_xml']),
        'shared': loads(request_dict['shared_xml']),
        'sla_parameters': loads(request_dict['filter_xml']),
      }
    )
    if (result.get('status', None) == 102):
      return ComputerPartition(
        request_dict=request_dict,
        connection_helper=self._connection_helper,
      )

    computer_partition = ComputerPartition(
      result['compute_node_id'],
      result['compute_partition_id'],
      connection_helper=self._connection_helper,
    )
    computer_partition._updateComputerPartitionInformation(result)
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
    # type: () -> str
    if not self._software_release:
      raise NameError('software_release has not been defined.')
    else:
      return self._software_release

  def error(self, error_log, logger=None):
    # Does not follow interface
    try:
      self._connection_helper.callJsonRpcAPI(
        'slapos.put.software_installation',
        {
          "portal_type": "Software Installation",
          'software_release_uri': self.getURI(),
          'compute_node_id': self.getComputerId(),
          "reported_state": "error",
          'error_status': str(error_log)
        }
      )
    except (RequestException, ConnectionError):
      # Do not block the caller if the connection
      # to the slapos master fails
      (logger or fallback_logger).exception('')

  def available(self):
    # if getattr(self, '_known_state', 'unknown') != "available":
    # Not required to repost if not needed.
    self._connection_helper.callJsonRpcAPI(
      'slapos.put.software_installation',
      {
        "portal_type": "Software Installation",
        'compute_node_id': self.getComputerId(),
        'software_release_uri': self.getURI(),
        'reported_state': 'available'
      }
    )

  def building(self):
    # if getattr(self, '_known_state', 'unknown') != "building":
    self._connection_helper.callJsonRpcAPI(
      'slapos.put.software_installation',
      {
        "portal_type": "Software Installation",
        'compute_node_id': self.getComputerId(),
        'software_release_uri': self.getURI(),
        'reported_state': 'building'
      }
    )

  def destroyed(self):
    self._connection_helper.callJsonRpcAPI(
      'slapos.put.software_installation',
      {
        "portal_type": "Software Installation",
        'compute_node_id': self.getComputerId(),
        'software_release_uri': self.getURI(),
        'reported_state': 'destroyed'
      }
    )

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
    self._connection_helper.callJsonRpcAPI(
      'slapos.post.v0.software_installation',
      {
        'reference': computer_guid,
        'software_release_uri': software_release,
        'state': state
      }
    )


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


@implementer(interface.IComputer)
class Computer(SlapDocument):

  def __init__(self, computer_id, connection_helper=None, hateoas_navigator=None):
    SlapDocument.__init__(self, connection_helper, hateoas_navigator)
    self._computer_id = computer_id

  def __getinitargs__(self):
    return (self._computer_id, )

  def getSoftwareReleaseList(self):
    """
    Returns the list of software release which has to be supplied by the
    computer.
    """
    if getattr(self, '__software_release_list', None) is None:
      # Sync the software release list on demand
      allDocs_dict = self._connection_helper.callJsonRpcAPI(
        'slapos.allDocs.software_installation',
        {
          'compute_node_id': self._computer_id,
          'portal_type': 'Software Installation'
        }
      )
      # XXX check if full page
      # XXX use a yield instead
      self.__software_release_list = []
      for result in allDocs_dict['result_list']:
        software_release_document = SoftwareRelease(
          software_release=result['software_release_uri'],
          computer_guid=result['compute_node_id'])
        software_release_document._requested_state = result['state']
        software_release_document._connection_helper = self._connection_helper
        software_release_document._hateoas_navigator = self._hateoas_navigator
        self.__software_release_list.append(software_release_document)
    return self.__software_release_list

  def getComputerPartitionList(self):
    # type: (...) -> Sequence[ComputerPartition]
    if getattr(self, '__computer_partition_list', None) is None:
      # Sync the computer partition list on demand
      allDocs_dict = self._connection_helper.callJsonRpcAPI(
        'slapos.allDocs.instance',
        {
          'compute_node_id': self._computer_id,
          'portal_type': 'Software Instance'
        }
      )
      # XXX check if full page
      # XXX use a yield instead
      self.__computer_partition_list = []
      for result in allDocs_dict['result_list']:
        # XXX duplicated with registerComputerPartition
        computer_partition = ComputerPartition(
          self._computer_id,
          result['compute_partition_id']
        )
        computer_partition._connection_helper = self._connection_helper
        computer_partition._hateoas_navigator = self._hateoas_navigator

        # XXX duplicated with fetchPartitionInfo
        computer_partition._instance_guid = result['reference']
        computer_partition._requested_state = result['state']
        computer_partition._software_release_document = SoftwareRelease(
          software_release=result['software_release_uri'],
          computer_guid=self._computer_id
        )

        self.__computer_partition_list.append(computer_partition)

    # Create a new list to prevent caller to change it
    return [x for x in self.__computer_partition_list]

  def reportUsage(self, computer_usage):
    if computer_usage == "":
      return
    self._connection_helper.POST('useComputer', data={
      'computer_id': self._computer_id,
      'use_string': computer_usage})

  def updateConfiguration(self, compute_partition_list):
    return self._connection_helper.callJsonRpcAPI(
      'slapos.put.compute_node',
      {
        "portal_type": "Compute Node",
        'compute_node_id': self._computer_id,
        'compute_partition_list': compute_partition_list
      }
    )

  def bang(self, message):
    return self._connection_helper.callJsonRpcAPI(
      'slapos.put.compute_node',
      {
        "portal_type": "Compute Node",
        'compute_node_id': self._computer_id,
        'bang_status_message': message
      }
    )

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
    # self._updateTransactionFile(partition_reference=None)

  def __getinitargs__(self):
    return (self._computer_id, self._partition_id, self._request_dict)

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
    self._connection_helper.callJsonRpcAPI(
      'slapos.put.v0.instance_reported_state',
      {
        "reference": self.getInstanceGuid(),
        "state": "destroyed"
      }
    )

  def started(self):
    self._connection_helper.callJsonRpcAPI(
      'slapos.put.v0.instance_reported_state',
      {
        "reference": self.getInstanceGuid(),
        "state": "started"
      }
    )

  def stopped(self):
    self._connection_helper.callJsonRpcAPI(
      'slapos.put.v0.instance_reported_state',
      {
        "reference": self.getInstanceGuid(),
        "state": "stopped"
      }
    )

  def error(self, error_log, logger=None):
    try:
      self._connection_helper.callJsonRpcAPI(
        'slapos.put.v0.instance_error',
        {
          "reference": self.getInstanceGuid(),
          "message": str(error_log)
        }
      )
    except (RequestException, ConnectionError):
      # Do not block the caller if the connection
      # to the slapos master fails
      (logger or fallback_logger).exception('')

  def bang(self, message):
    return self._connection_helper.callJsonRpcAPI(
      'slapos.put.v0.instance_bang',
      {
        "reference": self.getInstanceGuid(),
        'message': message
      }
    )

  def rename(self, new_name, slave_reference=None):
    post_dict = {
      'title': new_name,
      "reference": self.getInstanceGuid()
    }
    if slave_reference:
      post_dict['reference'] = slave_reference
    else:
      post_dict['reference'] = self.getInstanceGuid()
    self._connection_helper.callJsonRpcAPI(
      'slapos.put.v0.instance_title',
      post_dict
    )

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
    # type: (...) -> str
    return self._partition_id

  def getInstanceGuid(self):
    """Return instance_guid. Raise ResourceNotReady if it doesn't exist."""
    if not hasattr(self, '_instance_guid'):
      self._fetchComputerPartitionInformation()
    if self._instance_guid is None:
      raise ResourceNotReady()
    return self._instance_guid

  def getState(self):
    """return _requested_state. Raise ResourceNotReady if it doesn't exist."""
    if not hasattr(self, '_requested_state'):
      self._fetchComputerPartitionInformation()
    if self._requested_state is None:
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

  def _updateComputerPartitionInformation(self, result):
    computer_partition = self
    computer_partition._instance_guid = result['reference']
    computer_partition._requested_state = result['state']
    computer_partition._software_release_document = SoftwareRelease(
      software_release=result['software_release_uri'],
      computer_guid=self._computer_id
    )
    computer_partition._parameter_dict = result['parameters']
    if result['processing_timestamp'] is not None:
      computer_partition._parameter_dict['timestamp'] = result['processing_timestamp']
    # computer_partition._filter_dict = result['sla_parameters']
    computer_partition._connection_dict = result['connection_parameters']
    computer_partition._parameter_dict['ip_list'] = result['ip_list']
    computer_partition._parameter_dict['full_ip_list'] = result['full_ip_list']

    computer_partition._parameter_dict['instance_title'] = result['title']
    computer_partition._parameter_dict['root_instance_title'] = result['root_instance_title']

    computer_partition._parameter_dict['slap_software_type'] = result['software_type']
    computer_partition._parameter_dict['slap_computer_partition_id'] = self.getId()
    computer_partition._parameter_dict['slap_computer_id'] = self._computer_id
    computer_partition._parameter_dict['slap_software_release_url'] = result['software_release_uri']
    # XXX XXX XXX TODO implement slave instance support
    computer_partition._parameter_dict['slave_instance_list'] = result.get("slave_instance_list", [])

  def _fetchComputerPartitionInformation(self):
    result = self._connection_helper.callJsonRpcAPI(
      'slapos.get.software_instance',
      {
        "portal_type": "Software Instance",
        'compute_node_id': self._computer_id,
        'compute_partition_id': self.getId()
      }
    )

    # Sync the shared instances
    allDocs_shared_dict = self._connection_helper.callJsonRpcAPI(
      'slapos.allDocs.instance',
      {
        'host_instance_reference': result['reference'],
        'portal_type': 'Slave Instance'
      }
    )
    # XXX check if full page
    # XXX use a yield instead
    result['slave_instance_list'] = []
    for shared_item in allDocs_shared_dict['result_list']:
      shared_result = self._connection_helper.callJsonRpcAPI(
        'slapos.get.software_instance',
        {
          "portal_type": "Slave Instance",
          'reference': shared_item['reference']
        }
      )
      if shared_result['state'] == 'started':
        result['slave_instance_list'].append({
          'slave_title': shared_result['title'],
          'slap_software_type': shared_result['software_type'],
          'slave_reference': shared_result['reference'],
          'timestamp': shared_result['processing_timestamp'],
          'xml': dumps(shared_result['parameters']),
          'connection_xml': dumps(shared_result['connection_parameters'])
        })

    self._updateComputerPartitionInformation(result)

  def getInstanceParameterDict(self):
    # type: (...) -> Mapping[str, object]
    if not hasattr(self, '_parameter_dict'):
      self._fetchComputerPartitionInformation()
    return self._parameter_dict or {}

  def getConnectionParameterDict(self):
    # type: (...) -> Mapping[str, str]
    if not hasattr(self, '_connection_dict'):
      self._fetchComputerPartitionInformation()
    connection_dict = self._connection_dict
    if connection_dict is None:
      # XXX Backward compatibility for older slapproxy (<= 1.0.0)
      connection_dict = xml2dict(getattr(self, 'connection_xml', ''))
    return connection_dict or {}

  def getSoftwareRelease(self):
    # type: (...) -> SoftwareRelease
    """
    Returns the software release associate to the computer partition.
    """
    if not hasattr(self, '_software_release_document'):
      self._fetchComputerPartitionInformation()
    if self._software_release_document is None:
      raise NotFoundError("No software release information for partition %s" %
          self.getId())
    return self._software_release_document

  def setConnectionDict(self, connection_dict, slave_reference=None):
    if slave_reference is None:
      # Update a Software Instance
      # get the reference from the current documents
      slave_reference = self.getInstanceGuid()

    json_dict = {
      'reference': slave_reference,
      'connection_parameter_dict': connection_dict
    }

    self._connection_helper.callJsonRpcAPI(
      'slapos.put.v0.instance_connection_parameter',
      json_dict
    )

  def getInstanceParameter(self, key):
    parameter_dict = self.getInstanceParameterDict()
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
    return self._connection_helper.callJsonRpcAPI(
      'slapos.get.software_instance_certificate',
      {
        "portal_type": "Software Instance Certificate Record",
        "reference": self.getInstanceGuid(),
      }
    )

  def getStatus(self):
    return self.getAccessStatus()

  def getFullHostingIpAddressList(self):
    raise NotImplementedError('getFullHostingIpAddressList')
    """
    if getattr(self, '_connection_dict', None) is None:
      self._fetchComputerPartitionInformation()
    return self._parameter_dict['full_ip_list']
    xml = self._connection_helper.GET('getHostingSubscriptionIpList',
            params={
                'computer_id': self._computer_id,
                'computer_partition_id': self._partition_id,
                }
            )
    return loads(xml)
"""
  """
  def setComputerPartitionRelatedInstanceList(self, instance_reference_list):
    self._connection_helper.POST('updateComputerPartitionRelatedInstanceList',
        data={
          'computer_id': self._computer_id,
          'computer_partition_id': self._partition_id,
          'instance_reference_xml': dumps(instance_reference_list)
          }
        )"""

class SlapConnectionHelper(ConnectionHelper):

  def getComputerInformation(self, computer_id):
    xml = self.GET('getComputerInformation', params={'computer_id': computer_id})
    return loads(xml)

  def getFullComputerInformation(self, computer_id):
    """
    Retrieve from SlapOS Master Computer instance containing all needed
    informations (Software Releases, Computer Partitions, ...).
    """
    return Computer(computer_id)


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

    computer_partition = ComputerPartition(
      computer_guid,
      partition_id
    )
    computer_partition._connection_helper = self._connection_helper
    computer_partition._hateoas_navigator = self._hateoas_navigator
    return computer_partition

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

