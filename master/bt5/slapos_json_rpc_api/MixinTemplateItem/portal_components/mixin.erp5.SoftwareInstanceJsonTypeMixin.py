##############################################################################
#
# Copyright (c) 2024 Nexedi SA and Contributors. All Rights Reserved.
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
from Products.ERP5Type.UnrestrictedMethod import UnrestrictedMethod
from erp5.component.module.SlapOSCloud import _assertACI


class SoftwareInstanceJsonTypeMixin:

  # Declarative security
  security = ClassSecurityInfo()

  def getSlapTimestamp(self):
    return self._getSlapTimestamp()

  @UnrestrictedMethod
  def _getSlapTimestamp(self):
    compute_partition = self.getAggregateValue(portal_type="Compute Partition")
    if compute_partition is None:
      return int(self.getModificationDate())
    timestamp = int(compute_partition.getModificationDate())

    newtimestamp = int(self.getBangTimestamp(int(self.getModificationDate())))
    if (newtimestamp > timestamp):
      timestamp = newtimestamp

    # Check if any of the Shared instances hosted in the software instance have been reprocessed
    # XXX In the current what shared instances are processed, they cannot be reprocessed if the
    # host instance is not processed
    if (self.getPortalType() == "Software Instance"):
      shared_instance_sql_list = self.getPortalObject().portal_catalog.unrestrictedSearchResults(
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
          if (newtimestamp > timestamp):
            timestamp = newtimestamp

    return timestamp

  security.declareProtected(Permissions.AccessContentsInformation,
    'asJSONText')
  def asJSONText(self):
    try:
      parameter_dict = self._asParameterDict()
    except ValueError:
      parameter_dict = {}

    requested_state = self.getSlapState()
    if requested_state == "stop_requested":
      state = 'stopped'
    elif requested_state == "start_requested":
      state = 'started'
    elif requested_state == "destroy_requested":
      state = 'destroyed'
    elif requested_state == "draft":
      state = 'draft'
    else:
      raise ValueError("Unknown slap state : %s" % requested_state)
    # software instance has to define an xml parameter
    result = {
      "title": self.getTitle().decode("UTF-8"),
      "instance_guid": self.getReference().decode("UTF-8"),
      "software_release_uri": self.getUrlString(),
      "software_type": self.getSourceReference().decode("UTF-8"),
      "state": state,
      "connection_parameters": self.getConnectionXmlAsDict(),
      "parameters": self.getInstanceXmlAsDict(),
      "shared": self.getPortalType() == "Slave Instance",
      "root_instance_title": parameter_dict.get("root_instance_title", ""),
      "ip_list": [list(x) for x in parameter_dict.get("ip_list", [])],
      "full_ip_list": [list(x) for x in parameter_dict.get("full_ip_list", [])],
      "sla_parameters": self.getSlaXmlAsDict(),
      "computer_guid": parameter_dict.get("slap_computer_id", ""),
      "compute_partition_id": parameter_dict.get("slap_computer_partition_id", ""),
      "processing_timestamp": self.getSlapTimestamp(),
      "access_status_message": self.getTextAccessStatus(),
      "portal_type": "Software Instance"#self.getPortalType(),
    }

    return result

