##############################################################################
#
# Copyright (c) 2008 Nexedi SA and Contributors. All Rights Reserved.
#                    Yusei TAHARA <yusei@nexedi.com>
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
from Products.ERP5Type import Permissions, PropertySheet
from erp5.component.document.Item import Item
from erp5.component.document.JSONType import JSONType

import json

class SoftwareInstallation(Item, JSONType):
  """
  This class represents a computer like personal computer, printer, router.
  """

  portal_type = 'Software Installation'
  add_permission = Permissions.AddPortalContent

  # Declarative security
  security = ClassSecurityInfo()
  security.declareObjectProtected(Permissions.AccessContentsInformation)

  # Declarative properties
  property_sheets = ( PropertySheet.TextDocument
                      , PropertySheet.JSONTypeConstraint
                      )

  security.declareProtected(Permissions.AccessContentsInformation,
    'asJSONText')
  def asJSONText(self):
    requested_state = self.getSlapState()
    if requested_state == "stop_requested":
      state = 'stopped'
    elif requested_state in ("start_requested", "started"):
      state = 'available'
    elif requested_state == "destroy_requested":
      state = 'destroyed'
    else:
      raise ValueError("Unknown slap state : %s" % requested_state)
    # software instance has to define an xml parameter
    status_dict = self.getAccessStatus()
    result = {
      "$schema": self.getJSONSchemaUrl(),
      "reference": self.getReference().decode("UTF-8"),
      "software_release_uri": self.getUrlString(),
      "compute_node_id": self.getAggregateReference(),
      "state": state,
      "reported_state": status_dict.get("state"),
      "status_message": status_dict.get("text"),
      "processing_timestamp": self.getSlapTimestamp(),
    }
    result.update()
    return json.dumps(result, indent=2)

  def getSlapTimestamp(self):
    return int(self.getModificationDate())

  security.declareProtected(Permissions.AccessContentsInformation,
    'getJSONSchemaUrl')
  def getJSONSchemaUrl(self):
    """
    This is an attempt to provide stability to the Schema URL and by extension to asJSONText
    """
    portal = self.getPortalObject()
    portal_type_path = portal.portal_types.restrictedTraverse(self.getPortalType())
    base_url = portal.portal_preferences.getPreferredSlaposWebSiteUrl().strip("/")
    return "/".join([base_url, portal_type_path.getRelativeUrl(), "getTextContent"])