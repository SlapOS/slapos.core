# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2012 Nexedi SA and Contributors. All Rights Reserved.
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
from erp5.component.test.testSlapOSERP5GroupRoleSecurity import TestSlapOSGroupRoleSecurityMixin

class TestSlapOSLocalPermissionSlapOSInteractionWorkflow(
    TestSlapOSGroupRoleSecurityMixin):
  def _makePerson(self):
    new_id = self.generateNewId()
    self.person_user = self.portal.person_module\
                                  .newContent(portal_type="Person")
    self.person_user.edit(
      title="live_test_%s" % new_id,
      reference="live_test_%s" % new_id,
    )
    self.person_reference = self.person_user.getReference()
    self.person_user_id = self.person_user.getUserId()


  def test_ComputeNode_reindexObject(self):
    compute_node = self.portal.compute_node_module\
        .newContent(portal_type="Compute Node")
    self.tic()
    comment = 'recursiveReindexObject triggered on reindexObject'
    def verify_recursiveReindexObject_call(self, *args, **kw):
      if self.getRelativeUrl() == compute_node.getRelativeUrl():
        if compute_node.workflow_history['edit_workflow'][-1]['comment'] != comment:
          compute_node.portal_workflow.doActionFor(compute_node, action='edit_action',
          comment=comment)
      else:
        return self.recursiveReindexObject_call(*args, **kw)

    # Replace recursiveReindexObject by a dummy method
    from Products.ERP5Type.Core.Folder import Folder
    Folder.recursiveReindexObject_call = Folder.recursiveReindexObject
    Folder.recursiveReindexObject = verify_recursiveReindexObject_call
    try:
      compute_node.reindexObject()
      self.tic()
    finally:
      Folder.recursiveReindexObject = Folder.recursiveReindexObject_call
    self.assertEqual(comment,
        compute_node.workflow_history['edit_workflow'][-1]['comment'])


  def test_Person_setReference(self):
    # Due the change of security the interaction workflow don't trigger
    # updateLocalRolesOnSecurityGroups.

    person = self.portal.person_module.newContent(portal_type='Person')
    self.assertSecurityGroup(person, [self.user_id, 'F-ACCMAN',
      'F-SALEAGT', 'F-ACCAGT', 'F-SALEMAN'], False)

    person.edit(reference='TESTPER-%s' % self.generateNewId())
    self.commit()

    self.assertSecurityGroup(person, [self.user_id, 'F-ACCMAN',
      'F-SALEAGT', 'F-ACCAGT', 'F-SALEMAN'], False)

  def test_Person_newContent(self):
    person = self.portal.person_module.newContent(portal_type='Person')
    self.assertSecurityGroup(person, [self.user_id, 'F-ACCMAN',
      'F-SALEAGT', 'F-ACCAGT', 'F-SALEMAN'], False)

    person.newContent(portal_type="ERP5 Login")
    self.commit()

    self.assertSecurityGroup(person, [self.user_id, 'F-ACCMAN',
      'F-SALEAGT', 'F-ACCAGT', 'F-SALEMAN',
        person.getUserId(), 'SHADOW-%s' % person.getUserId()], False)


  def test_IntegrationSite_reindexObject(self):
    integration_site = self.portal.portal_integrations.newContent(
        portal_type="Integration Site")
    self.tic()
    comment = 'recursiveReindexObject triggered on reindexObject'
    def verify_recursiveReindexObject_call(self, *args, **kw):
      if self.getRelativeUrl() == integration_site.getRelativeUrl():
        if integration_site.workflow_history['edit_workflow'][-1]['comment'] != comment:
          integration_site.portal_workflow.doActionFor(integration_site, action='edit_action',
          comment=comment)
      else:
        return self.recursiveReindexObject_call(*args, **kw)

    # Replace recursiveReindexObject by a dummy method
    from Products.ERP5Type.Core.Folder import Folder
    Folder.recursiveReindexObject_call = Folder.recursiveReindexObject
    Folder.recursiveReindexObject = verify_recursiveReindexObject_call
    try:
      integration_site.reindexObject()
      self.tic()
    finally:
      Folder.recursiveReindexObject = Folder.recursiveReindexObject_call
    self.assertEqual(comment,
        integration_site.workflow_history['edit_workflow'][-1]['comment'])


  def test_RestrictedAccessToken_setAgent(self):
    self._makePerson()
    token = self.portal.access_token_module.newContent(
        portal_type='Restricted Access Token')

    self.assertSecurityGroup(token, [self.user_id],
        False)

    token.edit(
        agent=self.person_user.getRelativeUrl())
    self.commit()

    self.assertSecurityGroup(token, [self.user_id,
        self.person_user.getUserId()],
        False)

