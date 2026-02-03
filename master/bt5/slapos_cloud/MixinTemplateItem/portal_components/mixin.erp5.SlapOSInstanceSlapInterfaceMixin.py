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


class SlapOSInstanceSlapInterfaceMixin:

  # Declarative security
  security = ClassSecurityInfo()

  security.declarePrivate('_bangRequesterInstance')
  def _bangRequesterInstance(self):
    instance = self
    portal = instance.getPortalObject()
    for requester_instance in portal.portal_catalog(
      portal_type="Software Instance",
      successor__uid=instance.getUid()
    ):
      requester_instance.getObject().bang(
        bang_tree=False,
        comment="%s parameters changed" % instance.getRelativeUrl())

  security.declareProtected(Permissions.ModifyPortalContent, 'updateConnection')
  def updateConnection(self, connection_xml):
    instance = self

    if instance.getConnectionXml() == connection_xml:
      # Do not edit the document if nothing changed
      return

    instance.edit(connection_xml=connection_xml)
    # Prevent storing broken XML in text content (which prevent to update parameters after)
    instance.Base_checkConsistency()

    instance.setLastData(connection_xml)

    # Finally, inform requester instances of the change
    instance._bangRequesterInstance()


