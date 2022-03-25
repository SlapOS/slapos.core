# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2010 Nexedi SARL and Contributors. All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
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
from AccessControl import ClassSecurityInfo
from Products.ERP5Type import Permissions
from erp5.component.document.Item import Item
from lxml import etree
import collections

from AccessControl import Unauthorized
from AccessControl.Permissions import access_contents_information
from AccessControl import getSecurityManager
from Products.ERP5Type.UnrestrictedMethod import UnrestrictedMethod

from zLOG import LOG, INFO
try:
  from slapos.slap.slap import \
    SoftwareInstance as SlapSoftwareInstance
  from slapos.util import xml2dict
except ImportError:
  def xml2dict(dictionary):
    raise ImportError
  class SlapSoftwareInstance:
    def __init__(self):
      raise ImportError

def _assertACI(document):
  sm = getSecurityManager()
  if sm.checkPermission(access_contents_information,
      document):
    return document
  raise Unauthorized('User %r has no access to %r' % (sm.getUser(), document))

class DisconnectedSoftwareTree(Exception):
  pass

class CyclicSoftwareTree(Exception):
  pass

class SoftwareInstance(Item):
  """
  """

  meta_type = 'ERP5 Software Instance'
  portal_type = 'Software Instance'
  add_permission = Permissions.AddPortalContent

  # Declarative security
  security = ClassSecurityInfo()
  security.declareObjectProtected(Permissions.AccessContentsInformation)


  def _getXmlAsDict(self, xml):
    result_dict = {}
    if xml:
      tree = etree.fromstring(xml)
      for element in tree.iterfind('parameter'):
        key = element.get('id').encode("UTF-8")
        value = result_dict.get(key, None)
        if value is not None:
          value = (value + ' ' + element.text)
        else:
          value = element.text
        if value is not None:
          value = value.encode("UTF-8")
        result_dict[key] = value
    return result_dict

  security.declareProtected(Permissions.AccessContentsInformation,
    'getSlaXmlAsDict')
  def getSlaXmlAsDict(self):
    """Returns SLA XML as python dictionary"""
    return self._getXmlAsDict(self.getSlaXml())

  security.declareProtected(Permissions.AccessContentsInformation,
    'getInstanceXmlAsDict')
  def getInstanceXmlAsDict(self):
    """Returns Instance XML as python dictionary"""
    return self._getXmlAsDict(self.getTextContent())

  security.declareProtected(Permissions.AccessContentsInformation,
    'getConnectionXmlAsDict')
  def getConnectionXmlAsDict(self):
    """Returns Connection XML as python dictionary"""
    return self._getXmlAsDict(self.getConnectionXml())

  security.declareProtected(Permissions.AccessContentsInformation,
    'checkNotCyclic')
  def checkNotCyclic(self, graph):
    # see http://neopythonic.blogspot.com/2009/01/detecting-cycles-in-directed-graph.html
    todo = set(graph.keys())
    while todo:
      node = todo.pop()
      stack = [node]
      while stack:
        top = stack[-1]
        for node in graph[top]:
          if node in stack:
            raise CyclicSoftwareTree
          if node in todo:
            stack.append(node)
            todo.remove(node)
            break
        else:
          node = stack.pop()
    return True

  security.declareProtected(Permissions.AccessContentsInformation,
    'checkConnected')
  def checkConnected(self, graph, root):
    size = len(graph)
    visited = set()
    to_crawl = collections.deque(graph[root])
    while to_crawl:
      current = to_crawl.popleft()
      if current in visited:
        continue
      visited.add(current)
      node_children = set(graph[current])
      to_crawl.extend(node_children - visited)
    # add one to visited, as root won't be visited, only children
    # this is false positive in case of cyclic graphs, but they are
    # anyway wrong in Software Instance trees
    if size != len(visited) + 1:
      raise DisconnectedSoftwareTree
    return True

  def _instanceXmlToDict(self, xml):
    result_dict = {}
    try:
      result_dict = xml2dict(xml)
    except (etree.XMLSchemaError, etree.XMLSchemaParseError, # pylint: disable=catching-non-exception
      etree.XMLSchemaValidateError, etree.XMLSyntaxError): # pylint: disable=catching-non-exception
      LOG('SoftwareInstance', INFO, 'Issue during parsing xml:', error=True)
    return result_dict

  def _asSoftwareInstance(self):
    parameter_dict = self._asParameterDict()

    requested_state = self.getSlapState()
    if requested_state == "stop_requested":
      state = 'stopped'
    elif requested_state == "start_requested":
      state = 'started'
    elif requested_state == "destroy_requested":
      state = 'destroyed'
    else:
      raise ValueError("Unknown slap state : %s" % requested_state)

    # software instance has to define an xml parameter
    xml = self._instanceXmlToDict(
      parameter_dict.pop('xml'))
    connection_xml = self._instanceXmlToDict(
      parameter_dict.pop('connection_xml'))
    filter_xml = self._instanceXmlToDict(
      parameter_dict.pop('filter_xml'))
    instance_guid = parameter_dict.pop('instance_guid')

    software_instance = SlapSoftwareInstance(**parameter_dict)
    software_instance._parameter_dict = xml
    software_instance._connection_dict = connection_xml
    software_instance._filter_dict = filter_xml
    software_instance._requested_state = state
    software_instance._instance_guid = instance_guid
    return software_instance

  @UnrestrictedMethod
  def _asParameterDict(self, shared_instance_sql_list=None):
    portal = self.getPortalObject()
    compute_partition = self.getAggregateValue(portal_type="Compute Partition")
    if compute_partition is None:
      raise ValueError("Instance isn't allocated to call _asParamterDict")
    timestamp = int(compute_partition.getModificationDate())

    newtimestamp = int(self.getBangTimestamp(int(self.getModificationDate())))
    if (newtimestamp > timestamp):
      timestamp = newtimestamp

    instance_tree = self.getSpecialiseValue()

    ip_list = []
    full_ip_list = []
    for internet_protocol_address in compute_partition.contentValues(portal_type='Internet Protocol Address'):
      # XXX - There is new values, and we must keep compatibility
      address_tuple = (
          internet_protocol_address.getNetworkInterface('').decode("UTF-8"),
          internet_protocol_address.getIpAddress().decode("UTF-8"))
      if internet_protocol_address.getGatewayIpAddress('') and \
        internet_protocol_address.getNetmask(''):
        address_tuple = address_tuple + (
              internet_protocol_address.getGatewayIpAddress().decode("UTF-8"),
              internet_protocol_address.getNetmask().decode("UTF-8"),
              internet_protocol_address.getNetworkAddress('').decode("UTF-8"))
        full_ip_list.append(address_tuple)
      else:
        ip_list.append(address_tuple)

    shared_instance_list = []
    if (self.getPortalType() == "Software Instance"):
      append = shared_instance_list.append
      if shared_instance_sql_list is None:
        shared_instance_sql_list = portal.portal_catalog.unrestrictedSearchResults(
          default_aggregate_uid=compute_partition.getUid(),
          portal_type='Slave Instance',
          validation_state="validated",
          **{"slapos_item.slap_state": "start_requested"}
        )
      for shared_instance in shared_instance_sql_list:
        shared_instance = _assertACI(shared_instance.getObject())
        # XXX Use catalog to filter more efficiently
        if shared_instance.getSlapState() == "start_requested":
          newtimestamp = int(shared_instance.getBangTimestamp(int(shared_instance.getModificationDate())))
          append({
            'slave_title': shared_instance.getTitle().decode("UTF-8"),
            'slap_software_type': \
                shared_instance.getSourceReference().decode("UTF-8"),
            'slave_reference': shared_instance.getReference().decode("UTF-8"),
            'timestamp': newtimestamp,
            'xml': shared_instance.getTextContent(),
            'connection_xml': shared_instance.getConnectionXml(),
          })
          if (newtimestamp > timestamp):
            timestamp = newtimestamp
    return {
      'instance_guid': self.getReference().decode("UTF-8"),
      'instance_title': self.getTitle().decode("UTF-8"),
      'root_instance_title': instance_tree.getTitle().decode("UTF-8"),
      'root_instance_short_title': instance_tree.getShortTitle().decode("UTF-8"),
      'xml': self.getTextContent(),
      'connection_xml': self.getConnectionXml(),
      'filter_xml': self.getSlaXml(),
      'slap_computer_id': \
        compute_partition.getParentValue().getReference().decode("UTF-8"),
      'slap_computer_partition_id': \
        compute_partition.getReference().decode("UTF-8"),
      'slap_software_type': \
        self.getSourceReference().decode("UTF-8"),
      'slap_software_release_url': \
        self.getUrlString().decode("UTF-8"),
      'slave_instance_list': shared_instance_list,
      'ip_list': ip_list,
      'full_ip_list': full_ip_list,
      'timestamp': "%i" % timestamp,
    }

  @UnrestrictedMethod
  def _getInstanceTreeIpList(self):
    if self.getSlapState() == 'destroy_requested':
      return []
    # Search instance tree
    instance_tree = self.getSpecialiseValue()
    while instance_tree and instance_tree.getPortalType() != "Instance Tree":
      instance_tree = instance_tree.getSpecialiseValue()
    ip_address_list = []
    for instance in instance_tree.getSpecialiseRelatedValueList(
                                              portal_type="Software Instance"):
      compute_partition = instance.getAggregateValue(portal_type="Compute Partition")
      if not compute_partition:
        continue
      for internet_protocol_address in compute_partition.contentValues(
                                      portal_type='Internet Protocol Address'):
        ip_address_list.append(
              (internet_protocol_address.getNetworkInterface('').decode("UTF-8"),
              internet_protocol_address.getIpAddress().decode("UTF-8"))
        )
    
    return ip_address_list