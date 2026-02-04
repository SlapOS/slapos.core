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


class SlapOSComputeNodeSlapInterfaceMixin:

  # Declarative security
  security = ClassSecurityInfo()

  security.declareProtected(Permissions.ModifyPortalContent, 'generateCertificate')
  def generateCertificate(self):
    compute_node = self

    for certificate_login in compute_node.objectValues(
      portal_type=["Certificate Login"]):
      if certificate_login.getValidationState() == "validated":
        self.REQUEST.set("compute_node_certificate", None)
        self.REQUEST.set("compute_node_key", None)
        raise ValueError('Certificate still active.')

    certificate_login = compute_node.newContent(
      portal_type="Certificate Login")
    certificate_dict = certificate_login.getCertificate()
    certificate_login.validate()

    self.REQUEST.set("compute_node_certificate", certificate_dict["certificate"])
    self.REQUEST.set("compute_node_key", certificate_dict["key"])

  security.declareProtected(Permissions.ModifyPortalContent, 'approveComputeNodeRegistration')
  def approveComputeNodeRegistration(self):
    compute_node = self
    portal = compute_node.getPortalObject()
    compute_node.edit(
      capacity_scope='open'
    )

    # Keep this extra call separated to be compabible
    # with interaction workflow whenever this is
    # updated.
    compute_node.edit(
      allocation_scope='open'
    )

    portal.portal_workflow.doActionFor(compute_node, 'validate_action')

  security.declareProtected(Permissions.ModifyPortalContent, 'revokeCertificate')
  def revokeCertificate(self):
    compute_node = self

    self.REQUEST.set('compute_node_certificate', None)
    self.REQUEST.set('compute_node_key', None)

    no_certificate = True
    for certificate_login in compute_node.objectValues(
      portal_type=["Certificate Login"]):
      if certificate_login.getValidationState() == "validated":
        certificate_login.invalidate()
        no_certificate = False

    if no_certificate:
      raise ValueError('No certificate')

  security.declarePrivate('_markHistory')
  def _markHistory(self, comment):
    portal_workflow = self.getPortalObject().portal_workflow
    last_workflow_item = portal_workflow.getInfoFor(ob=self,
                                            name='comment', wf_id='edit_workflow')
    if last_workflow_item != comment:
      portal_workflow.doActionFor(self, action='edit_action', comment=comment)

  security.declareProtected(Permissions.ModifyPortalContent, 'reportComputeNodeBang')
  def reportComputeNodeBang(self, comment=None):
    compute_node = self
    portal = compute_node.getPortalObject()
    compute_partition_uid_list = [x.getUid() for x in compute_node.contentValues(portal_type='Compute Partition') if x.getSlapState() == 'busy']

    if comment:
      message = 'bang: %s' % comment
    else:
      message = 'bang'
    self._markHistory(message)

    for instance_sql in portal.portal_catalog(
      default_aggregate_uid=compute_partition_uid_list,
      portal_type=["Software Instance", "Slave Instance"],
      validation_state='validated',
      # Try limiting conflicts on multiple instances of the same tree
      # example: monitor frontend
      group_by_list=['specialise_uid']
    ):
      instance = instance_sql.getObject()
      if instance.getSlapState() in ["start_requested", "stop_requested"]:
        # Increase priority to not block indexations
        # if there are many activities created
        instance.activate(priority=2).SoftwareInstance_bangAsSelf(
          relative_url=instance.getRelativeUrl(),
          reference=instance.getReference(),
          comment=comment
        )

    compute_node.setErrorStatus(message)

