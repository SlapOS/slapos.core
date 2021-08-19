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
from DateTime import DateTime

class TestSlapOSLocalPermissionSlapOSInteractionWorkflow(
    TestSlapOSGroupRoleSecurityMixin):
  def _makePerson(self):
    new_id = self.generateNewId()
    self.person_user = self.portal.person_module.template_member.\
                                 Base_createCloneDocument(batch_mode=1)
    self.person_user.edit(
      title="live_test_%s" % new_id,
      reference="live_test_%s" % new_id,
    )
    self.person_reference = self.person_user.getReference()
    self.person_user_id = self.person_user.getUserId()

  def test_ComputerModel_edit(self):
    self._makePerson()
    model = self.portal.computer_model_module.newContent(
        portal_type='Computer Model')
    self.assertSecurityGroup(model, ['G-COMPANY', self.user_id], False)

    model.edit(source_administration=self.person_user.getRelativeUrl())
    self.commit()

    self.assertSecurityGroup(model,
        ['G-COMPANY', self.user_id, self.person_user_id], False)

  def test_ComputerNetwork_edit(self):
    self._makePerson()
    network = self.portal.computer_network_module.newContent(
        portal_type='Computer Network')
    self.assertSecurityGroup(network, ['G-COMPANY', self.user_id,
        'R-SHADOW-PERSON'], False)

    network.edit(source_administration=self.person_user.getRelativeUrl())
    self.commit()

    self.assertSecurityGroup(network,
        ['G-COMPANY', self.user_id, self.person_user_id, 'R-SHADOW-PERSON'],
        False)

  def test_ComputeNode_setUserId(self):
    compute_node = self.portal.compute_node_module.newContent(portal_type='Compute Node')
    self.assertSecurityGroup(compute_node, ['G-COMPANY', self.user_id, compute_node.getUserId()], False)

    compute_node.edit(user_id=None)
    self.commit()

    self.assertSecurityGroup(compute_node, ['G-COMPANY', self.user_id], False)

  def test_ComputeNode_setSourceAdministration(self):
    self._makePerson()
    compute_node = self.portal.compute_node_module.newContent(
        portal_type='Compute Node')
    self.assertSecurityGroup(compute_node, ['G-COMPANY', self.user_id, compute_node.getUserId()], False)

    compute_node.edit(source_administration=self.person_user.getRelativeUrl())
    self.commit()

    self.assertSecurityGroup(compute_node, ['G-COMPANY', self.user_id,
        self.person_user_id, compute_node.getUserId()], False)

  def test_ComputeNode_setAllocationScope(self):
    compute_node = self.portal.compute_node_module.newContent(portal_type='Compute Node')
    self.assertSecurityGroup(compute_node, ['G-COMPANY', self.user_id,
                                        compute_node.getUserId()], False)

    compute_node.edit(allocation_scope='open/public')
    self.commit()

    self.assertSecurityGroup(compute_node, ['G-COMPANY', self.user_id,
        'R-SHADOW-PERSON', compute_node.getUserId()], False)

  def test_ComputeNode_setDestinationSection(self):
    self._makePerson()
    compute_node = self.portal.compute_node_module.newContent(
        portal_type='Compute Node')
    self.assertSecurityGroup(compute_node, ['G-COMPANY', self.user_id,
                                        compute_node.getUserId()], False)

    compute_node.edit(source_administration=self.person_user.getRelativeUrl())
    self.commit()

    self.assertSecurityGroup(compute_node, ['G-COMPANY', self.user_id,
        self.person_user_id, compute_node.getUserId()], False)

  def test_ComputeNode_reindexObject(self):
    compute_node = self.portal.compute_node_module.template_compute_node\
        .Base_createCloneDocument(batch_mode=1)
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

  def test_InstanceTree_setReference(self):
    instance_tree = self.portal.instance_tree_module.newContent(
        portal_type='Instance Tree')
    self.assertSecurityGroup(instance_tree, [self.user_id,
        instance_tree.getId(), 'G-COMPANY'],
        False)

    instance_tree.edit(reference='TESTHS-%s' % self.generateNewId())
    self.commit()

    self.assertSecurityGroup(instance_tree, [self.user_id,
        instance_tree.getReference(), 'G-COMPANY'], False)

  def test_InstanceTree_setDestinationSection(self):
    self._makePerson()
    instance_tree = self.portal.instance_tree_module.newContent(
        portal_type='Instance Tree')
    self.assertSecurityGroup(instance_tree, [self.user_id,
        instance_tree.getId(), 'G-COMPANY'],
        False)

    instance_tree.edit(
        destination_section=self.person_user.getRelativeUrl())
    self.commit()

    self.assertSecurityGroup(instance_tree, [self.user_id,
        instance_tree.getId(), self.person_user.getUserId(),
        'G-COMPANY'],
        False)

  def test_Person_setReference(self):
    # Due the change of security the interaction workflow don't trigger
    # updateLocalRolesOnSecurityGroups.

    person = self.portal.person_module.newContent(portal_type='Person')
    self.assertSecurityGroup(person, [self.user_id, 'G-COMPANY'], False)

    person.edit(reference='TESTPER-%s' % self.generateNewId())
    self.commit()

    self.assertSecurityGroup(person, [self.user_id, 'G-COMPANY'], False)

  def test_Person_newContent(self):
    person = self.portal.person_module.newContent(portal_type='Person')
    self.assertSecurityGroup(person, [self.user_id, 'G-COMPANY'], False)

    person.newContent(portal_type="ERP5 Login")
    self.commit()

    self.assertSecurityGroup(person, [self.user_id, 'G-COMPANY',
        person.getUserId(), 'SHADOW-%s' % person.getUserId()], False)

  def test_SoftwareInstallation_setAggregate(self):
    installation = self.portal.software_installation_module.newContent(
        portal_type='Software Installation')
    self.assertSecurityGroup(installation, [self.user_id, 'G-COMPANY'], False)

    compute_node = self.portal.compute_node_module.newContent(portal_type='Compute Node',
        reference='TESTC-%s' % self.generateNewId())

    installation.edit(aggregate=compute_node.getRelativeUrl())
    self.commit()

    self.assertSecurityGroup(installation, [self.user_id, 'G-COMPANY',
        compute_node.getUserId()], False)


  def test_SoftwareInstallation_setDestinationSection(self):
    installation = self.portal.software_installation_module.newContent(
        portal_type='Software Installation')
    self.assertSecurityGroup(installation, [self.user_id, 'G-COMPANY'], False)

    self._makePerson()

    installation.edit(destination_section=self.person_user.getRelativeUrl())
    self.commit()

    self.assertSecurityGroup(installation, [self.user_id, 'G-COMPANY',
        self.person_user.getUserId()], False)

  def test_SoftwareInstance_setSpecialise(self):
    software_instance = self.portal.software_instance_module.newContent(
        portal_type='Software Instance')
    self.assertSecurityGroup(software_instance, [self.user_id, 'G-COMPANY'],
        False)

    instance_tree = self.portal.instance_tree_module.newContent(
        portal_type='Instance Tree', reference='TESTHS-%s' %
            self.generateNewId())
    software_instance.edit(specialise=instance_tree.getRelativeUrl())
    self.commit()

    self.assertSecurityGroup(software_instance, [self.user_id, 'G-COMPANY',
        instance_tree.getReference()], False)

  def test_SoftwareInstance_setAggregate(self):
    instance_tree = self.portal.instance_tree_module.newContent(
        portal_type='Instance Tree', reference='TESTHS-%s' %
            self.generateNewId())
    software_instance = self.portal.software_instance_module.newContent(
        portal_type='Software Instance',
        specialise=instance_tree.getRelativeUrl())
    self.assertSecurityGroup(software_instance, [self.user_id, 'G-COMPANY',
        instance_tree.getReference()],
        False)

    compute_node = self.portal.compute_node_module.template_compute_node\
        .Base_createCloneDocument(batch_mode=1)
    compute_node.edit(reference='TESTC-%s' % self.generateNewId())
    partition = compute_node.newContent(portal_type='Compute Partition')
    self.portal.portal_workflow._jumpToStateFor(partition, 'busy')
    self.assertSecurityGroup(partition, [self.user_id],
        True)
    software_instance.edit(aggregate=partition.getRelativeUrl())
    self.tic()

    self.assertSecurityGroup(software_instance, [self.user_id, 'G-COMPANY',
        compute_node.getUserId(), instance_tree.getReference()], False)
    self.assertSecurityGroup(partition, [self.user_id,
        instance_tree.getReference()], True)

  def test_SlaveInstance_setSpecialise(self):
    slave_instance = self.portal.software_instance_module.newContent(
        portal_type='Slave Instance')
    self.assertSecurityGroup(slave_instance, [self.user_id, 'G-COMPANY'],
        False)

    instance_tree = self.portal.instance_tree_module.newContent(
        portal_type='Instance Tree', reference='TESTHS-%s' %
            self.generateNewId())
    slave_instance.edit(specialise=instance_tree.getRelativeUrl())
    self.commit()

    self.assertSecurityGroup(slave_instance, [self.user_id, 'G-COMPANY',
        instance_tree.getReference()], False)

  def test_SlaveInstance_setAggregate(self):
    instance_tree = self.portal.instance_tree_module.newContent(
        portal_type='Instance Tree', reference='TESTHS-%s' %
            self.generateNewId())
    software_instance = self.portal.software_instance_module.newContent(
        portal_type='Software Instance',
        reference='TESTSO-%s' % self.generateNewId(),
        specialise=instance_tree.getRelativeUrl())
    software_instance.validate()
    slave_instance = self.portal.software_instance_module.newContent(
        portal_type='Slave Instance',
        specialise=instance_tree.getRelativeUrl())
    self.assertSecurityGroup(slave_instance, [self.user_id, 'G-COMPANY',
        instance_tree.getReference()],
        False)

    compute_node = self.portal.compute_node_module.template_compute_node\
        .Base_createCloneDocument(batch_mode=1)
    compute_node.edit(reference='TESTC-%s' % self.generateNewId())
    partition = compute_node.newContent(portal_type='Compute Partition')
    software_instance.edit(aggregate=partition.getRelativeUrl())
    self.portal.portal_workflow._jumpToStateFor(partition, 'busy')
    self.tic()

    slave_instance.edit(aggregate=partition.getRelativeUrl())

    self.assertSecurityGroup(slave_instance, [self.user_id, 'G-COMPANY',
        software_instance.getUserId(), compute_node.getUserId(),
        instance_tree.getReference()], False)

  def test_PaymentTransaction_setDestinationSection(self):
    self._makePerson()
    payment_transaction = self.portal.accounting_module.newContent(
        portal_type='Payment Transaction')
    self.assertSecurityGroup(payment_transaction, [self.user_id,
        'G-COMPANY', 'R-SHADOW-PERSON'],
        False)

    payment_transaction.edit(
        destination_section=self.person_user.getRelativeUrl())
    self.commit()

    self.assertSecurityGroup(payment_transaction, [self.user_id,
        'G-COMPANY', 'SHADOW-%s' % self.person_user.getUserId(),
        self.person_user.getUserId()],
        False)

  def test_PayzenEvent_setDestinationSection(self):
    self._makePerson()
    event = self.portal.system_event_module.newContent(
        portal_type='Payzen Event')
    self.assertSecurityGroup(event, [self.user_id,
        'G-COMPANY'],
        False)

    event.edit(
        destination_section=self.person_user.getRelativeUrl())
    self.commit()

    self.assertSecurityGroup(event, [self.user_id,
        'G-COMPANY', 'SHADOW-%s' % self.person_user.getUserId()],
        False)

  def test_WechatEvent_setDestinationSection(self):
    self._makePerson()
    event = self.portal.system_event_module.newContent(
        portal_type='Payzen Event')
    self.assertSecurityGroup(event, [self.user_id,
        'G-COMPANY'],
        False)

    event.edit(
        destination_section=self.person_user.getRelativeUrl())
    self.commit()

    self.assertSecurityGroup(event, [self.user_id,
        'G-COMPANY', 'SHADOW-%s' % self.person_user.getUserId()],
        False)

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

  def test_SaleInvoiceTransaction_setDestinationSection(self):
    self._makePerson()
    sale_invoice_transaction = self.portal.accounting_module.newContent(
        portal_type='Sale Invoice Transaction')
    self.assertSecurityGroup(sale_invoice_transaction, [self.user_id,
        'G-COMPANY', 'R-SHADOW-PERSON'],
        False)

    sale_invoice_transaction.edit(
        destination_section=self.person_user.getRelativeUrl())
    self.commit()

    self.assertSecurityGroup(sale_invoice_transaction, [self.user_id,
        'G-COMPANY', self.person_user.getUserId(), 'R-SHADOW-PERSON'],
        False)

  def test_SupportRequest_setDestinationDecision(self):
    self._makePerson()
    support_request = self.portal.support_request_module.newContent(
        portal_type='Support Request')
    self.assertSecurityGroup(support_request, ['G-COMPANY', self.user_id], False)

    support_request.edit(destination_decision=self.person_user.getRelativeUrl())
    self.commit()

    self.assertSecurityGroup(support_request, ['G-COMPANY', self.user_id,
        self.person_user_id], False)

  def test_RegularisationRequest_setDestinationDecision(self):
    self._makePerson()
    regularisation_request = self.portal.regularisation_request_module.newContent(
        portal_type='Regularisation Request')
    self.assertSecurityGroup(regularisation_request, ['G-COMPANY', self.user_id], False)

    regularisation_request.edit(destination_decision=self.person_user.getRelativeUrl())
    self.commit()

    self.assertSecurityGroup(regularisation_request, ['G-COMPANY', self.user_id,
        self.person_user_id], False)

  def test_Acknowledgement_setDestination(self):
    self._makePerson()
    event = self.portal.event_module.newContent(
        portal_type='Acknowledgement')
    self.assertSecurityGroup(event, ['G-COMPANY', self.user_id], False)

    event.edit(destination=self.person_user.getRelativeUrl())
    self.commit()

    self.assertSecurityGroup(event, ['G-COMPANY', self.user_id,
        self.person_user_id], False)

  def test_Acknowledgement_setSource(self):
    self._makePerson()
    event = self.portal.event_module.newContent(
        portal_type='Acknowledgement')
    self.assertSecurityGroup(event, ['G-COMPANY', self.user_id], False)

    event.edit(source=self.person_user.getRelativeUrl())
    self.commit()

    self.assertSecurityGroup(event, ['G-COMPANY', self.user_id,
        self.person_user_id], False)

  def test_FaxMessage_setDestination(self):
    self._makePerson()
    event = self.portal.event_module.newContent(
        portal_type='Fax Message')
    self.assertSecurityGroup(event, ['G-COMPANY', self.user_id], False)

    event.edit(destination=self.person_user.getRelativeUrl())
    self.commit()

    self.assertSecurityGroup(event, ['G-COMPANY', self.user_id,
        self.person_user_id], False)

  def test_FaxMessage_setSource(self):
    self._makePerson()
    event = self.portal.event_module.newContent(
        portal_type='Fax Message')
    self.assertSecurityGroup(event, ['G-COMPANY', self.user_id], False)

    event.edit(source=self.person_user.getRelativeUrl())
    self.commit()

    self.assertSecurityGroup(event, ['G-COMPANY', self.user_id,
        self.person_user_id], False)

  def test_Letter_setDestination(self):
    self._makePerson()
    event = self.portal.event_module.newContent(
        portal_type='Letter')
    self.assertSecurityGroup(event, ['G-COMPANY', self.user_id], False)

    event.edit(destination=self.person_user.getRelativeUrl())
    self.commit()

    self.assertSecurityGroup(event, ['G-COMPANY', self.user_id,
        self.person_user_id], False)

  def test_Letter_setSource(self):
    self._makePerson()
    event = self.portal.event_module.newContent(
        portal_type='Letter')
    self.assertSecurityGroup(event, ['G-COMPANY', self.user_id], False)

    event.edit(source=self.person_user.getRelativeUrl())
    self.commit()

    self.assertSecurityGroup(event, ['G-COMPANY', self.user_id,
        self.person_user_id], False)

  def test_MailMessage_setDestination(self):
    self._makePerson()
    event = self.portal.event_module.newContent(
        portal_type='Mail Message')
    self.assertSecurityGroup(event, ['G-COMPANY', self.user_id], False)

    event.edit(destination=self.person_user.getRelativeUrl())
    self.commit()

    self.assertSecurityGroup(event, ['G-COMPANY', self.user_id,
        self.person_user_id], False)

  def test_MailMessage_setSource(self):
    self._makePerson()
    event = self.portal.event_module.newContent(
        portal_type='Mail Message')
    self.assertSecurityGroup(event, ['G-COMPANY', self.user_id], False)

    event.edit(source=self.person_user.getRelativeUrl())
    self.commit()

    self.assertSecurityGroup(event, ['G-COMPANY', self.user_id,
        self.person_user_id], False)

  def test_Note_setDestination(self):
    self._makePerson()
    event = self.portal.event_module.newContent(
        portal_type='Note')
    self.assertSecurityGroup(event, ['G-COMPANY', self.user_id], False)

    event.edit(destination=self.person_user.getRelativeUrl())
    self.commit()

    self.assertSecurityGroup(event, ['G-COMPANY', self.user_id,
        self.person_user_id], False)

  def test_Note_setSource(self):
    self._makePerson()
    event = self.portal.event_module.newContent(
        portal_type='Note')
    self.assertSecurityGroup(event, ['G-COMPANY', self.user_id], False)

    event.edit(source=self.person_user.getRelativeUrl())
    self.commit()

    self.assertSecurityGroup(event, ['G-COMPANY', self.user_id,
        self.person_user_id], False)

  def test_PhoneCall_setDestination(self):
    self._makePerson()
    event = self.portal.event_module.newContent(
        portal_type='Phone Call')
    self.assertSecurityGroup(event, ['G-COMPANY', self.user_id], False)

    event.edit(destination=self.person_user.getRelativeUrl())
    self.commit()

    self.assertSecurityGroup(event, ['G-COMPANY', self.user_id,
        self.person_user_id], False)

  def test_PhoneCall_setSource(self):
    self._makePerson()
    event = self.portal.event_module.newContent(
        portal_type='Phone Call')
    self.assertSecurityGroup(event, ['G-COMPANY', self.user_id], False)

    event.edit(source=self.person_user.getRelativeUrl())
    self.commit()

    self.assertSecurityGroup(event, ['G-COMPANY', self.user_id,
        self.person_user_id], False)

  def test_ShortMessage_setDestination(self):
    self._makePerson()
    event = self.portal.event_module.newContent(
        portal_type='Short Message')
    self.assertSecurityGroup(event, ['G-COMPANY', self.user_id], False)

    event.edit(destination=self.person_user.getRelativeUrl())
    self.commit()

    self.assertSecurityGroup(event, ['G-COMPANY', self.user_id,
        self.person_user_id], False)

  def test_ShortMessage_setSource(self):
    self._makePerson()
    event = self.portal.event_module.newContent(
        portal_type='Short Message')
    self.assertSecurityGroup(event, ['G-COMPANY', self.user_id], False)

    event.edit(source=self.person_user.getRelativeUrl())
    self.commit()

    self.assertSecurityGroup(event, ['G-COMPANY', self.user_id,
        self.person_user_id], False)

  def test_SiteMessage_setDestination(self):
    self._makePerson()
    event = self.portal.event_module.newContent(
        portal_type='Site Message')
    self.assertSecurityGroup(event, ['G-COMPANY', self.user_id], False)

    event.edit(destination=self.person_user.getRelativeUrl())
    self.commit()

    self.assertSecurityGroup(event, ['G-COMPANY', self.user_id,
        self.person_user_id], False)

  def test_SiteMessage_setSource(self):
    self._makePerson()
    event = self.portal.event_module.newContent(
        portal_type='Site Message')
    self.assertSecurityGroup(event, ['G-COMPANY', self.user_id], False)

    event.edit(source=self.person_user.getRelativeUrl())
    self.commit()

    self.assertSecurityGroup(event, ['G-COMPANY', self.user_id,
        self.person_user_id], False)

  def test_Visit_setDestination(self):
    self._makePerson()
    event = self.portal.event_module.newContent(
        portal_type='Visit')
    self.assertSecurityGroup(event, ['G-COMPANY', self.user_id], False)

    event.edit(destination=self.person_user.getRelativeUrl())
    self.commit()

    self.assertSecurityGroup(event, ['G-COMPANY', self.user_id,
        self.person_user_id], False)

  def test_Visit_setSource(self):
    self._makePerson()
    event = self.portal.event_module.newContent(
        portal_type='Visit')
    self.assertSecurityGroup(event, ['G-COMPANY', self.user_id], False)

    event.edit(source=self.person_user.getRelativeUrl())
    self.commit()

    self.assertSecurityGroup(event, ['G-COMPANY', self.user_id,
        self.person_user_id], False)

  def test_WebMessage_setDestination(self):
    self._makePerson()
    event = self.portal.event_module.newContent(
        portal_type='Web Message')
    self.assertSecurityGroup(event, ['G-COMPANY', self.user_id], False)

    event.edit(destination=self.person_user.getRelativeUrl())
    self.commit()

    self.assertSecurityGroup(event, ['G-COMPANY', self.user_id,
        self.person_user_id], False)

  def test_WebMessage_setSource(self):
    self._makePerson()
    event = self.portal.event_module.newContent(
        portal_type='Web Message')
    self.assertSecurityGroup(event, ['G-COMPANY', self.user_id], False)

    event.edit(source=self.person_user.getRelativeUrl())
    self.commit()

    self.assertSecurityGroup(event, ['G-COMPANY', self.user_id,
        self.person_user_id], False)

  def test_SalePackingList_setSpecialise(self):
    self._makePerson()
    sale_packing_list = self.portal.sale_packing_list_module.newContent(
      destination_decision_value=self.person_user,
      portal_type='Sale Packing List')
    self.assertSecurityGroup(sale_packing_list, ['G-COMPANY', self.user_id], False)

    sale_packing_list.edit(
      specialise="sale_trade_condition_module/slapos_subscription_trade_condition")
    self.commit()

    self.assertSecurityGroup(sale_packing_list, ['G-COMPANY', self.user_id,
        self.person_user_id], False)

  def test_SalePackingList_setDestinationDecision(self):
    self._makePerson()
    sale_packing_list = self.portal.sale_packing_list_module.newContent(
      specialise="sale_trade_condition_module/slapos_subscription_trade_condition",
      portal_type='Sale Packing List')
    self.assertSecurityGroup(sale_packing_list, ['G-COMPANY', self.user_id], False)

    sale_packing_list.edit(
      destination_decision_value=self.person_user)
    self.commit()

    self.assertSecurityGroup(sale_packing_list, ['G-COMPANY', self.user_id,
        self.person_user_id], False)


  def test_RestrictedAccessToken_setAgent(self):
    self._makePerson()
    token = self.portal.access_token_module.newContent(
        portal_type='Restricted Access Token')

    self.assertSecurityGroup(token, [self.user_id,
        'G-COMPANY'],
        False)

    token.edit(
        agent=self.person_user.getRelativeUrl())
    self.commit()

    self.assertSecurityGroup(token, [self.user_id,
        'G-COMPANY', self.person_user.getUserId()],
        False)


  def test_InternalPackingListLine_setAggregate_instance_tree(self):
    self._makePerson()
    
    project = self.portal.project_module.newContent(
      portal_type="Project",
    )

    instance_tree = self.portal.instance_tree_module.newContent(
        portal_type='Instance Tree',
        reference='TESTHS-%s' % self.generateNewId())
    
    internal_packing_list = self.portal.internal_packing_list_module.newContent(
        portal_type='Internal Packing List')

    internal_packing_list_line = internal_packing_list.newContent(
        portal_type='Internal Packing List Line')

    internal_packing_list.edit(source_value=self.person_user,
                               source_section_value=self.person_user,
                             source_project_value=project,
                             destination=self.person_user.getRelativeUrl(),
                             destination_section=self.person_user.getRelativeUrl(),
                             source_decision=self.person_user.getRelativeUrl(),
                             destination_decision=self.person_user.getRelativeUrl(),
                             destination_project_value=project,
                             start_date=DateTime()-1,
                             stop_date=DateTime()-1)

    internal_packing_list.confirm()
    internal_packing_list.stop()
    internal_packing_list.deliver()

    software_instance = self.portal.software_instance_module.newContent(
        portal_type='Software Instance')
    software_instance.edit(specialise=instance_tree.getRelativeUrl())

    slave_instance = self.portal.software_instance_module.newContent(
        portal_type='Slave Instance')
    slave_instance.edit(specialise=instance_tree.getRelativeUrl())

    support_request = self.portal.support_request_module.newContent(
        portal_type="Support Request"
    )
    support_request.edit(aggregate=instance_tree.getRelativeUrl())
    upgrade_decision = self.portal.upgrade_decision_module.newContent(
        portal_type="Upgrade Decision"
    )
    upgrade_decision_line = upgrade_decision.newContent(
      portal_type="Upgrade Decision Line"
    )
    upgrade_decision_line.edit(aggregate=instance_tree.getRelativeUrl())
    self.tic()

    self.assertSecurityGroup(internal_packing_list, [self.user_id,],
        False)

    self.assertSecurityGroup(instance_tree, [self.user_id, 'G-COMPANY', 
        instance_tree.getReference()],
        False)

    self.assertSecurityGroup(software_instance, [self.user_id, 'G-COMPANY',
        instance_tree.getReference()], False)

    self.assertSecurityGroup(slave_instance, [self.user_id, 'G-COMPANY',
        instance_tree.getReference()], False)

    self.assertSecurityGroup(support_request, [self.user_id, 'G-COMPANY'], False)

    self.assertSecurityGroup(upgrade_decision, [self.user_id, 'G-COMPANY'], False)

    internal_packing_list_line.edit(
        #quantity_unit="unit",
        resource_value=self.portal.product_module.compute_node,
        price=0.0,
        quantity=1.0,
        aggregate_value=instance_tree)
    self.tic()

    self.assertSecurityGroup(internal_packing_list, [self.user_id,],
        False)

    self.assertSecurityGroup(instance_tree, [self.user_id, 'G-COMPANY', 
        project.getReference(),
        instance_tree.getReference()],
        False)

    self.assertSecurityGroup(software_instance, [self.user_id, 'G-COMPANY',
        project.getReference(),
        instance_tree.getReference()], False)

    self.assertSecurityGroup(slave_instance, [self.user_id, 'G-COMPANY',
        project.getReference(),
        instance_tree.getReference()], False)

    self.assertSecurityGroup(support_request, [self.user_id, 'G-COMPANY',
        project.getReference()], False)

    self.assertSecurityGroup(upgrade_decision, [self.user_id, 'G-COMPANY',
        project.getReference()], False)


  def test_InternalPackingListLine_setAggregate_compute_node(self):
    self._makePerson()
    
    project = self.portal.project_module.newContent(
      portal_type="Project",
    )
    
    compute_node = self.portal.compute_node_module.newContent(
        portal_type='Compute Node',
        reference='TESTCOMP-%s' % self.generateNewId())
    
    internal_packing_list = self.portal.internal_packing_list_module.newContent(
        portal_type='Internal Packing List')

    internal_packing_list_line = internal_packing_list.newContent(
        portal_type='Internal Packing List Line')

    internal_packing_list.edit(source_value=self.person_user,
                               source_section_value=self.person_user,
                             source_project_value=project,
                             destination=self.person_user.getRelativeUrl(),
                             destination_section=self.person_user.getRelativeUrl(),
                             source_decision=self.person_user.getRelativeUrl(),
                             destination_decision=self.person_user.getRelativeUrl(),
                             destination_project_value=project,
                             start_date=DateTime()-1,
                             stop_date=DateTime()-1)

    internal_packing_list.confirm()
    internal_packing_list.stop()
    internal_packing_list.deliver()

    installation = self.portal.software_installation_module.newContent(
        portal_type='Software Installation')
    installation.edit(aggregate=compute_node.getRelativeUrl())

    support_request = self.portal.support_request_module.newContent(
        portal_type="Support Request"
    )
    support_request.edit(aggregate=compute_node.getRelativeUrl())
    upgrade_decision = self.portal.upgrade_decision_module.newContent(
        portal_type="Upgrade Decision"
    )
    upgrade_decision_line = upgrade_decision.newContent(
      portal_type="Upgrade Decision Line"
    )
    upgrade_decision_line.edit(aggregate=compute_node.getRelativeUrl())
    self.tic()

    self.assertSecurityGroup(internal_packing_list, [self.user_id,],
        False)

    self.assertSecurityGroup(compute_node, [self.user_id, 'G-COMPANY',
        compute_node.getUserId()],
        False)
    
    self.assertSecurityGroup(installation, [self.user_id, 'G-COMPANY',
        compute_node.getUserId()], False)

    self.assertSecurityGroup(support_request, [self.user_id, 'G-COMPANY'], False)

    self.assertSecurityGroup(upgrade_decision, [self.user_id, 'G-COMPANY'], False)

    internal_packing_list_line.edit(
        #quantity_unit="unit",
        resource_value=self.portal.product_module.compute_node,
        price=0.0,
        quantity=1.0,
        aggregate_value=compute_node)
    self.tic()

    self.assertSecurityGroup(internal_packing_list, [self.user_id,],
        False)

    self.assertSecurityGroup(compute_node, [self.user_id, 'G-COMPANY',
        project.getReference(), compute_node.getUserId()],
        False)

    self.assertSecurityGroup(installation, [self.user_id, 'G-COMPANY',
        project.getReference(), compute_node.getUserId()], False)

    self.assertSecurityGroup(support_request, [self.user_id, 'G-COMPANY',
        project.getReference()], False)

    self.assertSecurityGroup(upgrade_decision, [self.user_id, 'G-COMPANY',
        project.getReference()], False)