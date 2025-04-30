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

import json

class ComputeNodeJsonTypeMixin:

  # Declarative security
  security = ClassSecurityInfo()

  security.declareProtected(Permissions.AccessContentsInformation,
    'asJSONText')
  def asJSONText(self):
    """
    Return a minimal representation of the Compute Node
    """
    compute_node_dict = {
      "$schema": self.getPortalObject().portal_types.restrictedTraverse(
        self.getPortalType()
        ).absolute_url()
        + "/getTextContent",
      "portal_type": "Compute Node",
      "computer_guid": self.getReference().decode("UTF-8"),
      "title": self.getTitle().decode("UTF-8"),
      "compute_partition_list": [],
      }

    compute_partition_list = self.contentValues(
      portal_type="Compute Partition",
      checked_permission="View"
    )
    for compute_partition in compute_partition_list:
      ip_list = []
      for internet_protocol_address in compute_partition.contentValues(portal_type='Internet Protocol Address'):
        ip_dict = {
          "ip-address": internet_protocol_address.getIpAddress().decode("UTF-8"),
          "network-interface": internet_protocol_address.getNetworkInterface('').decode("UTF-8"),
        }
        if internet_protocol_address.getGatewayIpAddress(''):
          ip_dict["gateway-ip-address"] = internet_protocol_address.getGatewayIpAddress('').decode("UTF-8")
        if internet_protocol_address.getNetmask(''):
          ip_dict["netmask"] = internet_protocol_address.getNetmask('').decode("UTF-8")
        if internet_protocol_address.getNetworkAddress(''):
          ip_dict["network-address"] = internet_protocol_address.getNetworkAddress('').decode("UTF-8")
        ip_list.append(ip_dict)
      compute_node_dict["compute_partition_list"].append({
        "partition_id": compute_partition.getReference(),
        "ip_list": ip_list,
      })
    return json.dumps(compute_node_dict, indent=2)
