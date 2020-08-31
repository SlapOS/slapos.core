# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2012 Nexedi SA and Contributors. All Rights Reserved.
#
# This program is free software: you can Use, Study, Modify and Redistribute
# it under the terms of the GNU General Public License version 3, or (at your
# option) any later version, as published by the Free Software Foundation.
#
# You can also Link and Combine this program with other software covered by
# the terms of any of the Free Software licenses or any of the Open Source
# Initiative approved licenses and Convey the resulting work. Corresponding
# source of such a combination shall include the source code for all other
# software used.
#
# This program is distributed WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See COPYING file for full licensing terms.
# See https://www.nexedi.com/licensing for rationale and options.
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

  def test_Computer_setUserId(self):
    computer = self.portal.computer_module.newContent(portal_type='Computer')
    self.assertSecurityGroup(computer, ['G-COMPANY', self.user_id, computer.getUserId()], False)

    computer.edit(user_id=None)
    self.commit()

    self.assertSecurityGroup(computer, ['G-COMPANY', self.user_id], False)

  def test_Computer_setSourceAdministration(self):
    self._makePerson()
    computer = self.portal.computer_module.newContent(
        portal_type='Computer')
    self.assertSecurityGroup(computer, ['G-COMPANY', self.user_id, computer.getUserId()], False)

    computer.edit(source_administration=self.person_user.getRelativeUrl())
    self.commit()

    self.assertSecurityGroup(computer, ['G-COMPANY', self.user_id,
        self.person_user_id, computer.getUserId()], False)

  def test_Computer_setAllocationScope(self):
    computer = self.portal.computer_module.newContent(portal_type='Computer')
    self.assertSecurityGroup(computer, ['G-COMPANY', self.user_id,
                                        computer.getUserId()], False)

    computer.edit(allocation_scope='open/public')
    self.commit()

    self.assertSecurityGroup(computer, ['G-COMPANY', self.user_id,
        'R-SHADOW-PERSON', computer.getUserId()], False)

  def test_Computer_setDestinationSection(self):
    self._makePerson()
    computer = self.portal.computer_module.newContent(
        portal_type='Computer')
    self.assertSecurityGroup(computer, ['G-COMPANY', self.user_id,
                                        computer.getUserId()], False)

    computer.edit(source_administration=self.person_user.getRelativeUrl())
    self.commit()

    self.assertSecurityGroup(computer, ['G-COMPANY', self.user_id,
        self.person_user_id, computer.getUserId()], False)

  def test_Computer_reindexObject(self):
    computer = self.portal.computer_module.template_computer\
        .Base_createCloneDocument(batch_mode=1)
    self.tic()
    comment = 'recursiveReindexObject triggered on reindexObject'
    def verify_recursiveReindexObject_call(self, *args, **kw):
      if self.getRelativeUrl() == computer.getRelativeUrl():
        if computer.workflow_history['edit_workflow'][-1]['comment'] != comment:
          computer.portal_workflow.doActionFor(computer, action='edit_action',
          comment=comment)
      else:
        return self.recursiveReindexObject_call(*args, **kw)

    # Replace recursiveReindexObject by a dummy method
    from Products.ERP5Type.Core.Folder import Folder
    Folder.recursiveReindexObject_call = Folder.recursiveReindexObject
    Folder.recursiveReindexObject = verify_recursiveReindexObject_call
    try:
      computer.reindexObject()
      self.tic()
    finally:
      Folder.recursiveReindexObject = Folder.recursiveReindexObject_call
    self.assertEqual(comment,
        computer.workflow_history['edit_workflow'][-1]['comment'])

  def test_HostingSubscription_setReference(self):
    hosting_subscription = self.portal.hosting_subscription_module.newContent(
        portal_type='Hosting Subscription')
    self.assertSecurityGroup(hosting_subscription, [self.user_id,
        hosting_subscription.getId(), 'G-COMPANY'],
        False)

    hosting_subscription.edit(reference='TESTHS-%s' % self.generateNewId())
    self.commit()

    self.assertSecurityGroup(hosting_subscription, [self.user_id,
        hosting_subscription.getReference(), 'G-COMPANY'], False)

  def test_HostingSubscription_setDestinationSection(self):
    self._makePerson()
    hosting_subscription = self.portal.hosting_subscription_module.newContent(
        portal_type='Hosting Subscription')
    self.assertSecurityGroup(hosting_subscription, [self.user_id,
        hosting_subscription.getId(), 'G-COMPANY'],
        False)

    hosting_subscription.edit(
        destination_section=self.person_user.getRelativeUrl())
    self.commit()

    self.assertSecurityGroup(hosting_subscription, [self.user_id,
        hosting_subscription.getId(), self.person_user.getUserId(),
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

    computer = self.portal.computer_module.newContent(portal_type='Computer',
        reference='TESTC-%s' % self.generateNewId())

    installation.edit(aggregate=computer.getRelativeUrl())
    self.commit()

    self.assertSecurityGroup(installation, [self.user_id, 'G-COMPANY',
        computer.getUserId()], False)


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

    hosting_subscription = self.portal.hosting_subscription_module.newContent(
        portal_type='Hosting Subscription', reference='TESTHS-%s' %
            self.generateNewId())
    software_instance.edit(specialise=hosting_subscription.getRelativeUrl())
    self.commit()

    self.assertSecurityGroup(software_instance, [self.user_id, 'G-COMPANY',
        hosting_subscription.getReference()], False)

  def test_SoftwareInstance_setAggregate(self):
    hosting_subscription = self.portal.hosting_subscription_module.newContent(
        portal_type='Hosting Subscription', reference='TESTHS-%s' %
            self.generateNewId())
    software_instance = self.portal.software_instance_module.newContent(
        portal_type='Software Instance',
        specialise=hosting_subscription.getRelativeUrl())
    self.assertSecurityGroup(software_instance, [self.user_id, 'G-COMPANY',
        hosting_subscription.getReference()],
        False)

    computer = self.portal.computer_module.template_computer\
        .Base_createCloneDocument(batch_mode=1)
    computer.edit(reference='TESTC-%s' % self.generateNewId())
    partition = computer.newContent(portal_type='Computer Partition')
    self.portal.portal_workflow._jumpToStateFor(partition, 'busy')
    self.assertSecurityGroup(partition, [self.user_id],
        True)
    software_instance.edit(aggregate=partition.getRelativeUrl())
    self.tic()

    self.assertSecurityGroup(software_instance, [self.user_id, 'G-COMPANY',
        computer.getUserId(), hosting_subscription.getReference()], False)
    self.assertSecurityGroup(partition, [self.user_id,
        hosting_subscription.getReference()], True)

  def test_SlaveInstance_setSpecialise(self):
    slave_instance = self.portal.software_instance_module.newContent(
        portal_type='Slave Instance')
    self.assertSecurityGroup(slave_instance, [self.user_id, 'G-COMPANY'],
        False)

    hosting_subscription = self.portal.hosting_subscription_module.newContent(
        portal_type='Hosting Subscription', reference='TESTHS-%s' %
            self.generateNewId())
    slave_instance.edit(specialise=hosting_subscription.getRelativeUrl())
    self.commit()

    self.assertSecurityGroup(slave_instance, [self.user_id, 'G-COMPANY',
        hosting_subscription.getReference()], False)

  def test_SlaveInstance_setAggregate(self):
    hosting_subscription = self.portal.hosting_subscription_module.newContent(
        portal_type='Hosting Subscription', reference='TESTHS-%s' %
            self.generateNewId())
    software_instance = self.portal.software_instance_module.newContent(
        portal_type='Software Instance',
        reference='TESTSO-%s' % self.generateNewId(),
        specialise=hosting_subscription.getRelativeUrl())
    software_instance.validate()
    slave_instance = self.portal.software_instance_module.newContent(
        portal_type='Slave Instance',
        specialise=hosting_subscription.getRelativeUrl())
    self.assertSecurityGroup(slave_instance, [self.user_id, 'G-COMPANY',
        hosting_subscription.getReference()],
        False)

    computer = self.portal.computer_module.template_computer\
        .Base_createCloneDocument(batch_mode=1)
    computer.edit(reference='TESTC-%s' % self.generateNewId())
    partition = computer.newContent(portal_type='Computer Partition')
    software_instance.edit(aggregate=partition.getRelativeUrl())
    self.portal.portal_workflow._jumpToStateFor(partition, 'busy')
    self.tic()

    slave_instance.edit(aggregate=partition.getRelativeUrl())

    self.assertSecurityGroup(slave_instance, [self.user_id, 'G-COMPANY',
        software_instance.getUserId(), computer.getUserId(),
        hosting_subscription.getReference()], False)

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


  def test_InternalPackingListLine_setAggregate_hosting_subscription(self):
    self._makePerson()
    
    project = self.portal.project_module.newContent(
      portal_type="Project",
    )

    hosting_subscription = self.portal.hosting_subscription_module.newContent(
        portal_type='Hosting Subscription',
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
    software_instance.edit(specialise=hosting_subscription.getRelativeUrl())

    slave_instance = self.portal.software_instance_module.newContent(
        portal_type='Slave Instance')
    slave_instance.edit(specialise=hosting_subscription.getRelativeUrl())
    self.tic()

    self.assertSecurityGroup(internal_packing_list, [self.user_id,],
        False)

    self.assertSecurityGroup(hosting_subscription, [self.user_id, 'G-COMPANY', 
        hosting_subscription.getReference()],
        False)

    self.assertSecurityGroup(software_instance, [self.user_id, 'G-COMPANY',
        hosting_subscription.getReference()], False)

    self.assertSecurityGroup(slave_instance, [self.user_id, 'G-COMPANY',
        hosting_subscription.getReference()], False)

    internal_packing_list_line.edit(
        #quantity_unit="unit",
        resource_value=self.portal.product_module.computer,
        price=0.0,
        quantity=1.0,
        aggregate_value=hosting_subscription)
    self.tic()

    self.assertSecurityGroup(internal_packing_list, [self.user_id,],
        False)

    self.assertSecurityGroup(hosting_subscription, [self.user_id, 'G-COMPANY', 
        project.getReference(),
        hosting_subscription.getReference()],
        False)

    self.assertSecurityGroup(software_instance, [self.user_id, 'G-COMPANY',
        project.getReference(),
        hosting_subscription.getReference()], False)

    self.assertSecurityGroup(slave_instance, [self.user_id, 'G-COMPANY',
        project.getReference(),
        hosting_subscription.getReference()], False)

  def test_InternalPackingListLine_setAggregate_computer(self):
    self._makePerson()
    
    project = self.portal.project_module.newContent(
      portal_type="Project",
    )
    
    computer = self.portal.computer_module.newContent(
        portal_type='Computer',
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
    installation.edit(aggregate=computer.getRelativeUrl())
    self.tic()

    self.assertSecurityGroup(internal_packing_list, [self.user_id,],
        False)

    self.assertSecurityGroup(computer, [self.user_id, 'G-COMPANY',
        computer.getUserId()],
        False)
    
    self.assertSecurityGroup(installation, [self.user_id, 'G-COMPANY',
        computer.getUserId()], False)

    internal_packing_list_line.edit(
        #quantity_unit="unit",
        resource_value=self.portal.product_module.computer,
        price=0.0,
        quantity=1.0,
        aggregate_value=computer)
    self.tic()

    self.assertSecurityGroup(internal_packing_list, [self.user_id,],
        False)

    self.assertSecurityGroup(computer, [self.user_id, 'G-COMPANY',
        project.getReference(), computer.getUserId()],
        False)

    self.assertSecurityGroup(installation, [self.user_id, 'G-COMPANY',
        project.getReference(), computer.getUserId()], False)
