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

from Products.ERP5Type.UnrestrictedMethod import UnrestrictedMethod
from erp5.component.module.SlapOSCloud import _assertACI
from Products.ERP5Type.Utils import unicode2str

from zLOG import LOG, INFO
try:
  from slapos.util import xml2dict, loads
except ImportError:
  def xml2dict(dictionary):
    raise ImportError
  def loads(*args):
    raise ImportError

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

  def _asSoftwareInstanceDict(self):
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

    software_instance_dict = parameter_dict
    software_instance_dict['_parameter_dict'] = xml
    software_instance_dict['_connection_dict'] = connection_xml
    software_instance_dict['_filter_dict'] = filter_xml
    software_instance_dict['_requested_state'] = state
    software_instance_dict['_instance_guid'] = instance_guid
    return software_instance_dict

  def _getModificationDateAsTimestamp(self, document):
    return int(float(document.getModificationDate()) * 1e6)

  @UnrestrictedMethod
  def _asParameterDict(self, shared_instance_sql_list=None):
    portal = self.getPortalObject()
    compute_partition = self.getAggregateValue(portal_type="Compute Partition")
    if compute_partition is None:
      raise ValueError("Instance isn't allocated to call _asParamterDict")

    timestamp = max(
      self._getModificationDateAsTimestamp(compute_partition),
      int(self.getBangTimestamp(self._getModificationDateAsTimestamp(self))))

    instance_tree = self.getSpecialiseValue()

    ip_list = []
    full_ip_list = []
    for internet_protocol_address in compute_partition.contentValues(portal_type='Internet Protocol Address'):
      # XXX - There is new values, and we must keep compatibility
      address_tuple = (
          unicode2str(internet_protocol_address.getNetworkInterface('')),
          unicode2str(internet_protocol_address.getIpAddress()))
      if internet_protocol_address.getGatewayIpAddress('') and \
        internet_protocol_address.getNetmask(''):
        address_tuple = address_tuple + (
              unicode2str(internet_protocol_address.getGatewayIpAddress()),
              unicode2str(internet_protocol_address.getNetmask()),
              unicode2str(internet_protocol_address.getNetworkAddress('')))
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
          shared_timestamp = int(shared_instance.getBangTimestamp(
              self._getModificationDateAsTimestamp(shared_instance)))

          append({
            'slave_title': unicode2str(shared_instance.getTitle()),
            'slap_software_type': \
                unicode2str(shared_instance.getSourceReference()),
            'slave_reference': unicode2str(shared_instance.getReference()),
            'timestamp': shared_timestamp,
            'xml': shared_instance.getTextContent(),
            'connection_xml': shared_instance.getConnectionXml(),
          })
          timestamp = max(timestamp, shared_timestamp)
    return {
      'instance_guid': unicode2str(self.getReference()),
      'instance_title': unicode2str(self.getTitle()),
      'root_instance_title': unicode2str(instance_tree.getTitle()),
      'root_instance_short_title': unicode2str(instance_tree.getShortTitle()),
      'xml': self.getTextContent(),
      'connection_xml': self.getConnectionXml(),
      'filter_xml': self.getSlaXml(),
      'slap_computer_id': \
        unicode2str(compute_partition.getParentValue().getReference()),
      'slap_computer_partition_id': \
        unicode2str(compute_partition.getReference()),
      'slap_software_type': \
        unicode2str(self.getSourceReference()),
      'slap_software_release_url': \
        unicode2str(self.getUrlString()),
      'slave_instance_list': shared_instance_list,
      'ip_list': ip_list,
      'full_ip_list': full_ip_list,
      'timestamp': timestamp,
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
              (unicode2str(internet_protocol_address.getNetworkInterface('')),
              unicode2str(internet_protocol_address.getIpAddress()))
        )
    
    return ip_address_list

  def _updateSucessorList(self, instance_reference_xml):
    """
    Update Software Instance successor list to match the given list. If one
    instance was not requested by this compute partition, it should be removed
    in the successor_list of this instance.
    Once the link is removed, this instance will be trashed by Garbage Collect!

    instance_reference_xml contain list of title of sub-instances requested by
    this instance.
    """
    cache_reference = '%s-PREDLIST' % self.getReference()
    if not self.isLastData(cache_reference, instance_reference_xml):
      instance_reference_list = loads(instance_reference_xml)
      current_successor_list = self.getSuccessorValueList(
                            portal_type=['Software Instance', 'Slave Instance'])
      current_successor_title_list = [i.getTitle() for i in current_successor_list]
      # If there are items to remove
      if list(set(current_successor_title_list).difference(instance_reference_list)) != []:
        successor_list = [instance.getRelativeUrl() for instance in
                            current_successor_list if instance.getTitle()
                            in instance_reference_list]

        LOG('SoftwareInstance', INFO, '%s : Updating successor list to %s' % (
            self.getReference(), successor_list), error=False)
        self.edit(successor_list=successor_list,
            comment='successor_list edited to unlink non commited instances')
      self.setLastData(instance_reference_xml, key=cache_reference)