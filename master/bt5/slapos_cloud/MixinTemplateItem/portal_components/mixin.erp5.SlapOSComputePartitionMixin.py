# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2010-2022 Nexedi SA and Contributors. All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsibility of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# guarantees and support are strongly advised to contract a Free Software
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
from erp5.component.module.SlapOSCloud import _assertACI
from zLOG import LOG, INFO
from OFS.Traversable import NotFound

try:
  from slapos.util import calculate_dict_hash
except ImportError:
  # Do no prevent instance from starting
  # if libs are not installed
  class SlapComputePartition:
    def __init__(self):
      raise ImportError
  class SoftwareRelease:
    def __init__(self):
      raise ImportError
  def calculate_dict_hash(*args):
    raise ImportError

class SlapOSComputePartitionMixin(object):

  def _getSoftwareInstance(self, slave_reference=None):
    if self.getSlapState() != 'busy':
      LOG('SlapOSComputePartitionMixin::_getSoftwareInstance', INFO,
          'Compute partition %s shall be busy, is free' %
          self.getRelativeUrl())
      raise NotFound("No software instance found for: %s - %s" % (
        self.getParentValue().getTitle(), self.getTitle()))
    else:
      query_kw = {
        'validation_state': 'validated',
        'portal_type': 'Slave Instance',
        'default_aggregate_uid': self.getUid(),
      }
      if slave_reference is None:
        query_kw['portal_type'] = "Software Instance"
      else:
        query_kw['reference'] = slave_reference

      software_instance = _assertACI(
        self.getPortalObject().portal_catalog.unrestrictedGetResultValue(**query_kw))
      if software_instance is None:
        raise NotFound("No software instance found for: %s - %s" % (
          self.getParentValue().getTitle(), self.getTitle()))
      else:
        return software_instance

  def _registerComputePartition(self):
    portal = self.getPortalObject()
    compute_node = self
    while compute_node.getPortalType() != 'Compute Node':
      compute_node = compute_node.getParentValue()
    compute_node_id = compute_node.getReference().decode("UTF-8")

    partition_dict = {
      "compute_node_id": compute_node_id,
      "partition_id": self.getReference().decode("UTF-8"),
      "_software_release_document": None,
      "_requested_state": 'destroyed',
      "_need_modification": 0
    }

    if self.getSlapState() == 'busy':
      software_instance_list = portal.portal_catalog.unrestrictedSearchResults(
          portal_type="Software Instance",
          default_aggregate_uid=self.getUid(),
          validation_state="validated",
          limit=2,
          )
      software_instance_count = len(software_instance_list)
      if software_instance_count == 1:
        software_instance = _assertACI(software_instance_list[0].getObject())
      elif software_instance_count > 1:
        # XXX do not prevent the system to work if one partition is broken
        raise NotImplementedError, "Too many instances %s linked to %s" % \
          ([x.path for x in software_instance_list],
           self.getRelativeUrl())

    if software_instance is not None:
      state = software_instance.getSlapState()
      if state == "stop_requested":
        partition_dict['_requested_state'] = 'stopped'
      if state == "start_requested":
        partition_dict['_requested_state'] = 'started'

      partition_dict['_software_release_document'] = {
            "software_release": software_instance.getUrlString().decode("UTF-8"),
            "computer_guid": compute_node_id
      }
      partition_dict['_access_status'] = software_instance.getTextAccessStatus()
      partition_dict["_need_modification"] = 1
      # trick client side, that data has been synchronised already for given
      # document
      partition_dict["_synced"] = True

      parameter_dict = software_instance._asParameterDict()
      # software instance has to define an xml parameter
      partition_dict["_parameter_dict"] = software_instance._instanceXmlToDict(
        parameter_dict.pop('xml'))
      partition_dict['_connection_dict'] = software_instance._instanceXmlToDict(
        parameter_dict.pop('connection_xml'))
      partition_dict['_filter_dict'] = software_instance._instanceXmlToDict(
        parameter_dict.pop('filter_xml'))
      partition_dict['_instance_guid'] = parameter_dict.pop('instance_guid')
      for slave_instance_dict in parameter_dict.get("slave_instance_list", []):
        if "connection_xml" in slave_instance_dict:
          connection_dict = software_instance._instanceXmlToDict(
            slave_instance_dict.pop("connection_xml"))
          slave_instance_dict.update(connection_dict)
          slave_instance_dict['connection-parameter-hash'] = \
            calculate_dict_hash(connection_dict)
        if "xml" in slave_instance_dict:
          slave_instance_dict.update(software_instance._instanceXmlToDict(
            slave_instance_dict.pop("xml")))
      partition_dict['_parameter_dict'].update(parameter_dict)

    return partition_dict
