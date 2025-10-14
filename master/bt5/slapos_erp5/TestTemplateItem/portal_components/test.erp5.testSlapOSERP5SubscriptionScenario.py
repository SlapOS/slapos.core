# -*- coding: utf8 -*-
##############################################################################
#
# Copyright (c) 2012 Nexedi SA and Contributors. All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsibility of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# guarantees and support are strongly adviced to contract a Free Software
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
##############################################################################

from erp5.component.test.testSlapOSERP5VirtualMasterScenario import TestSlapOSVirtualMasterScenarioMixin
from erp5.component.test.SlapOSTestCaseMixin import PinnedDateTime
from DateTime import DateTime


class TestSlapOSSubscriptionScenarioMixin(TestSlapOSVirtualMasterScenarioMixin):
  pass


class TestSlapOSSubscriptionScenario(TestSlapOSSubscriptionScenarioMixin):

  def test_subscription_request_cancel_after_instance_is_archived(self):
    """ It is only tested with is_virtual_master_accountable enabled since the
      subscription request is automatically validated/invalidated if price is 0.
    """
    with PinnedDateTime(self, DateTime('2024/01/31')):
      currency, _, _, sale_person, _ = self.bootstrapVirtualMasterTest()

      self.logout()
      # lets join as slapos administrator, which will manager the project
      project_owner_reference = 'project-%s' % self.generateNewId()
      project_owner_person = self.joinSlapOS(self.web_site, project_owner_reference)

      self.tic()
      self.logout()
      self.login(sale_person.getUserId())

      project_relative_url = self.addProject(
        is_accountable=True, person=project_owner_person, currency=currency)

      self.logout()

      self.login()
      project = self.portal.restrictedTraverse(project_relative_url)

      preference = self.portal.portal_preferences.slapos_default_system_preference
      preference.edit(
        preferred_subscription_assignment_category_list=[
          'function/customer',
          'role/client',
          'destination_project/%s' % project.getRelativeUrl()
        ]
      )

      public_server_software = self.generateNewSoftwareReleaseUrl()
      public_instance_type = 'public type'

      software_product, _, _ = self.addSoftwareProduct(
        "instance product", project, public_server_software, public_instance_type
      )

      self.logout()
      self.login(sale_person.getUserId())

      self.tic()
      sale_supply = self.portal.portal_catalog.getResultValue(
        portal_type='Sale Supply',
        source_project__uid=project.getUid()
      )
      sale_supply.newContent(
        portal_type="Sale Supply Line",
        base_price=9,
        resource_value=software_product
      )
      sale_supply.validate()

      self.tic()
      # some preparation
      self.logout()

      # lets join as slapos administrator, which will own few compute_nodes
      owner_reference = 'owner-%s' % self.generateNewId()
      owner_person = self.joinSlapOS(self.web_site, owner_reference)

      self.login()

      # first slapos administrator assignment can only be created by
      # the erp5 manager
      self.addProjectProductionManagerAssignment(owner_person, project)
      self.tic()

      self.login(project_owner_person.getUserId())

      # Pay deposit to validate virtual master
      deposit_amount = 42.0
      ledger = self.portal.portal_categories.ledger.automated
      
      outstanding_amount_list = project_owner_person.Entity_getOutstandingDepositAmountList(
          currency.getUid(), ledger_uid=ledger.getUid())
      amount = sum([i.total_price for i in outstanding_amount_list])
      self.assertEqual(amount, deposit_amount)
  
      # Ensure to pay from the website
      outstanding_amount = self.web_site.restrictedTraverse(outstanding_amount_list[0].getRelativeUrl())
      outstanding_amount.Base_createExternalPaymentTransactionFromOutstandingAmountAndRedirect()

      self.tic()
      self.logout()
      self.login()
      payment_transaction = self.portal.portal_catalog.getResultValue(
        portal_type="Payment Transaction",
        destination_section_uid=project_owner_person.getUid(),
        simulation_state="started"
      )
      self.assertEqual("deposit",
        payment_transaction.getSpecialiseValue().getTradeConditionType())
      # payzen/wechat or accountant will only stop the payment
      payment_transaction.stop()
      self.tic()
      self.assertNotEqual(None,
                      payment_transaction.receivable.getGroupingReference(None))
      self.login(project_owner_person.getUserId())

      amount = sum([i.total_price for i in project_owner_person.Entity_getOutstandingDepositAmountList(
          currency.getUid(), ledger_uid=ledger.getUid())])
      self.assertEqual(0, amount)

      self.logout()

      # join as the another visitor and request software instance on public
      # compute_node
      self.logout()
      public_reference = 'public-%s' % self.generateNewId()
      public_person = self.joinSlapOS(self.web_site, public_reference)
      self.login()


    with PinnedDateTime(self, DateTime('2024/02/17 01:01')):
      public_instance_title = 'Public title %s' % self.generateNewId()

      self.login(public_person.getUserId())

      self.personRequestInstanceNotReady(
        software_release=public_server_software,
        software_type=public_instance_type,
        partition_reference=public_instance_title,
        project_reference=project.getReference()
      )
      self.tic()

      instance_tree = self.portal.portal_catalog.getResultValue(
        portal_type="Instance Tree",
        title=public_instance_title,
        follow_up__reference=project.getReference()
      )
      person = instance_tree.getDestinationSectionValue()
      self.assertEqual(person.getUserId(), public_person.getUserId())

      subscription_request = self.checkServiceSubscriptionRequest(instance_tree, 'submitted')
      expected_deposit_amount = 9.0
      self.assertEqual(subscription_request.getTotalPrice(),
        expected_deposit_amount)

      self.tic()

      outstanding_amount_list = person.Entity_getOutstandingDepositAmountList(
            currency.getUid(), ledger_uid=subscription_request.getLedgerUid())

      self.assertEqual(sum([i.total_price for i in outstanding_amount_list]),
        expected_deposit_amount)

      self.login(public_person.getUserId())
      self.personRequestInstanceNotReady(
        software_release=public_server_software,
        software_type=public_instance_type,
        partition_reference=public_instance_title,
        state='<marshal><string>destroyed</string></marshal>',
        project_reference=project.getReference()
      )

      # let's find instances of user and check connection strings
      instance_tree_list = [q.getObject() for q in
          self._getCurrentInstanceTreeList()
          if q.getTitle() == public_instance_title]

      self.assertEqual(0, len(instance_tree_list))

      self.tic()
      subscription_request = self.checkServiceSubscriptionRequest(instance_tree, 'cancelled')

      self.logout()
      self.login()

    # Check stock
    # Instance was celled before generate simulation
    inventory_list = self.portal.portal_simulation.getCurrentInventoryList(**{
      'group_by_section': False,
      'group_by_node': True,
      'group_by_variation': True,
      'resource_uid': software_product.getUid(),
      'node_uid': public_person.getUid(),
      'project_uid': None,
      'ledger_uid': self.portal.portal_categories.ledger.automated.getUid()
    })
    self.assertEqual(len(inventory_list), 0)

    # Check accounting
    transaction_list = self.portal.account_module.receivable.Account_getAccountingTransactionList(
      mirror_section_uid=public_person.getUid())
    self.assertEqual(len(transaction_list), 0)

    self.login()

    # Ensure no unexpected object has been created
    # 2 accounting transaction / line
    # 5 assignment request
    # 2 credential request
    # 1 event
    # 1 instance tree
    # 1 open sale order / line
    # 5 (can reduce to 2) assignment
    # 4 simulation mvt
    # 2 packing list / line
    # 3 sale supply / line
    # 2 sale trade condition
    # 1 software product
    # 2 subscription requests
    self.assertRelatedObjectCount(project, 31)

    with PinnedDateTime(self, DateTime('2024/02/18 01:01')):
      self.checkERP5StateBeforeExit()

  def test_subscription_request_cancel_after_project_is_invalidated(self):
    """ It is only tested with is_virtual_master_accountable enabled since the
      subscription request is automatically validated/invalidated if price is 0.
    """
    with PinnedDateTime(self, DateTime('2024/01/31')):
      currency, _, _, sale_person, _ = self.bootstrapVirtualMasterTest()

      self.logout()
      # lets join as slapos administrator, which will manager the project
      project_owner_reference = 'project-%s' % self.generateNewId()
      project_owner_person = self.joinSlapOS(self.web_site, project_owner_reference)

      self.tic()
      self.logout()
      self.login(sale_person.getUserId())

      project_relative_url = self.addProject(
        is_accountable=True, person=project_owner_person, currency=currency)

      self.logout()
      self.login()
      project = self.portal.restrictedTraverse(project_relative_url)

      preference = self.portal.portal_preferences.slapos_default_system_preference
      preference.edit(
        preferred_subscription_assignment_category_list=[
          'function/customer',
          'role/client',
          'destination_project/%s' % project.getRelativeUrl()
        ]
      )

      self.logout()

      # lets join as slapos administrator, which will own few compute_nodes
      owner_reference = 'owner-%s' % self.generateNewId()
      owner_person = self.joinSlapOS(self.web_site, owner_reference)

      self.login()

      # first slapos administrator assignment can only be created by
      # the erp5 manager
      self.addProjectProductionManagerAssignment(owner_person, project)
      self.tic()

      self.login(project_owner_person.getUserId())

      # Pay deposit to validate virtual master
      deposit_amount = 42.0
      ledger = self.portal.portal_categories.ledger.automated

      outstanding_amount_list = project_owner_person.Entity_getOutstandingDepositAmountList(
          currency.getUid(), ledger_uid=ledger.getUid())
      amount = sum([i.total_price for i in outstanding_amount_list])
      self.assertEqual(amount, deposit_amount)

      self.login()

      # Invalidate Project to cancel subscription, there isnt a use case except
      # by Manager, but we would like to ensure it works, once the action is 
      # implemented.
      project.invalidate()

      self.tic()
      self.login()

      self.checkServiceSubscriptionRequest(project, 'cancelled')
      self.login(project_owner_person.getUserId())

      amount = sum([i.total_price for i in project_owner_person.Entity_getOutstandingDepositAmountList(
          currency.getUid(), ledger_uid=ledger.getUid())])
      self.assertEqual(0, amount)

      self.logout()

    self.login()

    # Check accounting
    transaction_list = self.portal.account_module.receivable.Account_getAccountingTransactionList(
      mirror_section_uid=project_owner_person.getUid())
    self.assertEqual(len(transaction_list),  0)

    # Ensure no unexpected object has been created
    # 4 assignment request
    # 1 credential request
    # 4 assignment
    # 2 Sale Supply + Line
    # 2 Sale Trade condition
    # 1 subscription request
    self.assertRelatedObjectCount(project, 14)
    self.checkERP5StateBeforeExit()

  def test_subscription_request_cancel_after_compute_node_is_invalidated(self):
    """ It is only tested with is_virtual_master_accountable enabled since the
      subscription request is automatically validated/invalidated if price is 0.
    """
    with PinnedDateTime(self, DateTime('2024/01/31')):
      currency, _, _, sale_person, _ = self.bootstrapVirtualMasterTest()

      self.logout()
      # lets join as slapos administrator, which will manager the project
      project_owner_reference = 'project-%s' % self.generateNewId()
      project_owner_person = self.joinSlapOS(self.web_site, project_owner_reference)

      self.tic()
      self.logout()
      self.login(sale_person.getUserId())

      project_relative_url = self.addProject(
        is_accountable=True, person=project_owner_person, currency=currency)

      self.logout()
      self.login()
      project = self.portal.restrictedTraverse(project_relative_url)

      preference = self.portal.portal_preferences.slapos_default_system_preference
      preference.edit(
        preferred_subscription_assignment_category_list=[
          'function/customer',
          'role/client',
          'destination_project/%s' % project.getRelativeUrl()
        ]
      )

      public_server_software = self.generateNewSoftwareReleaseUrl()
      public_instance_type = 'public type'

      software_product, release_variation, type_variation = self.addSoftwareProduct(
        "instance product", project, public_server_software, public_instance_type
      )

      self.logout()
      self.login(sale_person.getUserId())

      self.tic()
      sale_supply = self.portal.portal_catalog.getResultValue(
        portal_type='Sale Supply',
        source_project__uid=project.getUid()
      )
      sale_supply.searchFolder(
        portal_type='Sale Supply Line',
        resource__relative_url="service_module/slapos_compute_node_subscription"
      )[0].edit(base_price=99)
      sale_supply.newContent(
        portal_type="Sale Supply Line",
        base_price=9,
        resource_value=software_product
      )
      sale_supply.validate()

      self.tic()
      # some preparation
      self.logout()

      # lets join as slapos administrator, which will own few compute_nodes
      owner_reference = 'owner-%s' % self.generateNewId()
      owner_person = self.joinSlapOS(self.web_site, owner_reference)

      self.login()
      # first slapos administrator assignment can only be created by
      # the erp5 manager
      self.addProjectProductionManagerAssignment(owner_person, project)
      self.tic()

      self.login(project_owner_person.getUserId())

      # Pay deposit to validate virtual master
      deposit_amount = 42.0
      ledger = self.portal.portal_categories.ledger.automated

      outstanding_amount_list = project_owner_person.Entity_getOutstandingDepositAmountList(
          currency.getUid(), ledger_uid=ledger.getUid())
      amount = sum([i.total_price for i in outstanding_amount_list])
      self.assertEqual(amount, deposit_amount)

      # Ensure to pay from the website
      outstanding_amount = self.web_site.restrictedTraverse(outstanding_amount_list[0].getRelativeUrl())
      outstanding_amount.Base_createExternalPaymentTransactionFromOutstandingAmountAndRedirect()

      self.tic()
      self.logout()
      self.login()
      payment_transaction = self.portal.portal_catalog.getResultValue(
        portal_type="Payment Transaction",
        destination_section_uid=project_owner_person.getUid(),
        simulation_state="started"
      )
      self.assertEqual(payment_transaction.getSpecialiseValue().getTradeConditionType(), "deposit")
      # payzen/wechat or accountant will only stop the payment
      payment_transaction.stop()
      self.tic()
      self.assertNotEqual(None,
                      payment_transaction.receivable.getGroupingReference(None))
      self.login(project_owner_person.getUserId())
      amount = sum([i.total_price for i in project_owner_person.Entity_getOutstandingDepositAmountList(
          currency.getUid(), ledger_uid=ledger.getUid())])
      self.assertEqual(0, amount)

      self.logout()

      # hooray, now it is time to create compute_nodes
      self.login(owner_person.getUserId())

      public_server_title = 'Public Server for %s' % owner_reference
      public_server_id = self.requestComputeNode(public_server_title, project.getReference())
      public_server = self.portal.portal_catalog.getResultValue(
          portal_type='Compute Node', reference=public_server_id)
      self.setAccessToMemcached(public_server)
      self.assertNotEqual(None, public_server)
      self.setServerOpenPublic(public_server)
      public_server.generateCertificate()

      self.addAllocationSupply("for compute node", public_server, software_product,
                               release_variation, type_variation)

      # and install some software on them
      self.supplySoftware(public_server, public_server_software)

      # format the compute_nodes
      self.formatComputeNode(public_server)
      self.logout()

      self.tic()
      self.login(project_owner_person.getUserId())

      # Pay deposit to validate virtual master
      deposit_amount = 102.36
      ledger = self.portal.portal_categories.ledger.automated

      outstanding_amount_list = project_owner_person.Entity_getOutstandingDepositAmountList(
          currency.getUid(), ledger_uid=ledger.getUid())
      amount = sum([i.total_price for i in outstanding_amount_list])
      self.assertAlmostEqual(amount, deposit_amount)

      self.login()

      # Invalidate Public Computer to cancel subscription we would like to ensure 
      # it works, once the action is implemented.
      public_server.invalidate()

      self.tic()
      self.login()

      self.checkServiceSubscriptionRequest(public_server, 'cancelled')
      self.login(project_owner_person.getUserId())

      amount = sum([i.total_price for i in project_owner_person.Entity_getOutstandingDepositAmountList(
          currency.getUid(), ledger_uid=ledger.getUid())])
      self.assertEqual(0, amount)

      self.logout()

    self.login()

    # Check accounting
    transaction_list = self.portal.account_module.receivable.Account_getAccountingTransactionList(
      mirror_section_uid=project_owner_person.getUid())
    self.assertEqual(len(transaction_list),  2)

    # Ensure no unexpected object has been created
    # 2 accounting transaction / line
    # 3 allocation supply / Line / Cell
    # 4 assignment request
    # 1 compute node
    # 1 credential request
    # 1 event
    # 1 open sale order / line
    # 4  assignment
    # 4 simulation mvt
    # 2 packing list / line
    # 3 sale supply / line
    # 2 sale trade condition
    # 1 software installation
    # 1 software product
    # 2 subscription requests
    self.assertRelatedObjectCount(project, 32)

    with PinnedDateTime(self, DateTime('2024/02/01')):
      self.checkERP5StateBeforeExit()

  def checkInstanceAllocationFromPayableToFree(self,
      person_user_id, person_reference,
      instance_title, software_release, software_type, server,
      project_reference, deposit_amount, currency, sale_person):

    self.login(person_user_id)

    self.personRequestInstanceNotReady(
      software_release=software_release,
      software_type=software_type,
      partition_reference=instance_title,
      project_reference=project_reference
    )
    self.tic()

    instance_tree = self.portal.portal_catalog.getResultValue(
      portal_type="Instance Tree",
      title=instance_title,
      follow_up__reference=project_reference
    )
    person = instance_tree.getDestinationSectionValue()
    self.assertEqual(person.getUserId(), person_user_id)

    subscription_request = self.checkServiceSubscriptionRequest(instance_tree, 'submitted')
    self.assertEqual(subscription_request.getTotalPrice(), deposit_amount)

    self.tic()

    outstanding_amount_list = person.Entity_getOutstandingDepositAmountList(
          currency.getUid(), ledger_uid=subscription_request.getLedgerUid())

    self.assertEqual(sum([i.total_price for i in outstanding_amount_list]), deposit_amount)

    # XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
    self.logout()
    self.login(sale_person.getUserId())
    #previous_trade_condition = subscription_request.getSpecialiseValue()
    subscription_request.SubscriptionRequest_changeFromPayableToFree(None)
    self.tic()
    self.logout()

    self.login(person.getUserId())
    # Ensure to pay from the website
    #outstanding_amount = self.web_site.restrictedTraverse(outstanding_amount_list[0].getRelativeUrl())
    #outstanding_amount.Base_createExternalPaymentTransactionFromOutstandingAmountAndRedirect()

    self.tic()
    self.logout()
    self.login()
    payment_transaction = self.portal.portal_catalog.getResultValue(
      portal_type="Payment Transaction",
      destination_section_uid=person.getUid(),
      simulation_state="started"
    )
    self.assertEqual(payment_transaction, None)

    self.login(person_user_id)

    self.checkServiceSubscriptionRequest(instance_tree, 'cancelled')

    amount = sum([i.total_price for i in person.Entity_getOutstandingDepositAmountList(
          currency.getUid(), ledger_uid=subscription_request.getLedgerUid())])
    self.assertEqual(0, amount)

    self.login(person_user_id)
    self.personRequestInstance(
      software_release=software_release,
      software_type=software_type,
      partition_reference=instance_title,
      project_reference=project_reference
    )

    # now instantiate it on compute_node and set some nice connection dict
    self.simulateSlapgridCP(server)

    # let's find instances of user and check connection strings
    instance_tree_list = [q.getObject() for q in
        self._getCurrentInstanceTreeList()
        if q.getTitle() == instance_title]
    self.assertEqual(1, len(instance_tree_list))
    instance_tree = instance_tree_list[0]

    software_instance = instance_tree.getSuccessorValue()
    self.assertEqual(software_instance.getTitle(),
        instance_tree.getTitle())
    connection_dict = software_instance.getConnectionXmlAsDict()
    self.assertSameSet(('url_1', 'url_2'), connection_dict.keys())
    self.login()
    partition = software_instance.getAggregateValue()
    self.assertSameSet(
        ['http://%s/' % q.getIpAddress() for q in
            partition.contentValues(portal_type='Internet Protocol Address')],
        connection_dict.values())

  def test_virtual_master_with_accounting_scenario_from_payable_to_free(self):
    with PinnedDateTime(self, DateTime('2024/02/17')):
      currency, _, _, sale_person, _ = self.bootstrapVirtualMasterTest()

      self.logout()
      # lets join as slapos administrator, which will manager the project
      project_owner_reference = 'project-%s' % self.generateNewId()
      project_owner_person = self.joinSlapOS(self.web_site, project_owner_reference)

      self.login()
      self.tic()
      self.logout()
      self.login(sale_person.getUserId())

      project_relative_url = self.addProject(
        is_accountable=True, person=project_owner_person, currency=currency)

      self.logout()

      self.login()
      project = self.portal.restrictedTraverse(project_relative_url)

      preference = self.portal.portal_preferences.slapos_default_system_preference
      preference.edit(
        preferred_subscription_assignment_category_list=[
          'function/customer',
          'role/client',
          'destination_project/%s' % project.getRelativeUrl()
        ]
      )

      public_server_software = self.generateNewSoftwareReleaseUrl()
      public_instance_type = 'public type'

      software_product, release_variation, type_variation = self.addSoftwareProduct(
        "instance product", project, public_server_software, public_instance_type
      )

      self.logout()
      self.login(sale_person.getUserId())

      self.tic()
      sale_supply = self.portal.portal_catalog.getResultValue(
        portal_type='Sale Supply',
        source_project__uid=project.getUid()
      )
      sale_supply.searchFolder(
        portal_type='Sale Supply Line',
        resource__relative_url="service_module/slapos_compute_node_subscription"
      )[0].edit(base_price=99)
      sale_supply.newContent(
        portal_type="Sale Supply Line",
        base_price=9,
        resource_value=software_product
      )
      sale_supply.validate()

      self.tic()
      # some preparation
      self.logout()

      # lets join as slapos administrator, which will own few compute_nodes
      owner_reference = 'owner-%s' % self.generateNewId()
      owner_person = self.joinSlapOS(self.web_site, owner_reference)

      self.login()
      # first slapos administrator assignment can only be created by
      # the erp5 manager
      self.addProjectProductionManagerAssignment(owner_person, project)
      self.tic()

      # hooray, now it is time to create compute_nodes
      self.login(owner_person.getUserId())

      public_server_title = 'Public Server for %s' % owner_reference
      public_server_id = self.requestComputeNode(public_server_title, project.getReference())
      public_server = self.portal.portal_catalog.getResultValue(
          portal_type='Compute Node', reference=public_server_id)
      self.setAccessToMemcached(public_server)
      self.assertNotEqual(None, public_server)
      self.setServerOpenPublic(public_server)
      public_server.generateCertificate()

      self.addAllocationSupply("for compute node", public_server, software_product,
                               release_variation, type_variation)

      # and install some software on them
      self.supplySoftware(public_server, public_server_software)

      # format the compute_nodes
      self.formatComputeNode(public_server)
      self.logout()
      self.login(project_owner_person.getUserId())

      # Pay deposit to validate virtual master + one computer
      deposit_amount = 42.0 + 99.0
      ledger = self.portal.portal_categories.ledger.automated

      outstanding_amount_list = project_owner_person.Entity_getOutstandingDepositAmountList(
          currency.getUid(), ledger_uid=ledger.getUid())
      amount = sum([i.total_price for i in outstanding_amount_list])
      self.assertEqual(amount, deposit_amount)

      # Ensure to pay from the website
      outstanding_amount = self.web_site.restrictedTraverse(outstanding_amount_list[0].getRelativeUrl())
      outstanding_amount.Base_createExternalPaymentTransactionFromOutstandingAmountAndRedirect()

      self.tic()
      self.logout()
      self.login()
      payment_transaction = self.portal.portal_catalog.getResultValue(
        portal_type="Payment Transaction",
        destination_section_uid=project_owner_person.getUid(),
        simulation_state="started"
      )
      self.assertEqual(payment_transaction.getSpecialiseValue().getTradeConditionType(), "deposit")
      # payzen/wechat or accountant will only stop the payment
      payment_transaction.stop()
      self.tic()
      self.assertNotEqual(None,
                      payment_transaction.receivable.getGroupingReference(None))
      self.login(project_owner_person.getUserId())

      amount = sum([i.total_price for i in project_owner_person.Entity_getOutstandingDepositAmountList(
          currency.getUid(), ledger_uid=ledger.getUid())])
      self.assertEqual(0, amount)

      self.logout()

      # join as the another visitor and request software instance on public
      # compute_node
      self.logout()
      public_reference = 'public-%s' % self.generateNewId()
      public_person = self.joinSlapOS(self.web_site, public_reference)
      self.login()

    with PinnedDateTime(self, DateTime('2024/02/17 01:01')):
      public_instance_title = 'Public title %s' % self.generateNewId()

      # Request a payable instance without deposit
      # Change the subscription from payable to free
      self.checkInstanceAllocationFromPayableToFree(public_person.getUserId(),
          public_reference, public_instance_title,
          public_server_software, public_instance_type,
          public_server, project.getReference(),
          9.0, currency, sale_person)

      self.login()
      public_person = self.portal.portal_catalog.getResultValue(
        portal_type='ERP5 Login', reference=public_reference).getParentValue()
      self.login(owner_person.getUserId())

      # and the instances
      self.checkInstanceUnallocation(public_person.getUserId(),
          public_reference, public_instance_title,
          public_server_software, public_instance_type, public_server,
          project.getReference())

      # and uninstall some software on them
      self.logout()
      self.login(owner_person.getUserId())
      self.supplySoftware(public_server, public_server_software,
                          state='destroyed')

      self.logout()
      # Uninstall from compute_node
      self.login()
      self.simulateSlapgridSR(public_server)

      self.tic()

    # Check stock
    inventory_list = self.portal.portal_simulation.getCurrentInventoryList(**{
      'group_by_section': False,
      'group_by_node': True,
      'group_by_variation': True,
      'resource_uid': software_product.getUid(),
      'node_uid': public_person.getUid(),
      'project_uid': None,
      'ledger_uid': self.portal.portal_categories.ledger.automated.getUid()
    })
    self.assertEqual(len(inventory_list), 1)
    self.assertEqual(inventory_list[0].quantity, 1)
    resource_vcl = [
      # 'software_release/%s' % release_variation.getRelativeUrl(),
      'software_type/%s' % type_variation.getRelativeUrl()
    ]
    resource_vcl.sort()
    self.assertEqual(resource_vcl,
       inventory_list[0].getVariationCategoryList(),
       "%s %s" % (resource_vcl, inventory_list[0].getVariationCategoryList()))

    # Check accounting
    transaction_list = self.portal.account_module.receivable.Account_getAccountingTransactionList(
      mirror_section_uid=public_person.getUid())
    self.assertEqual(len(transaction_list),  0)

    self.login()

    # Ensure no unexpected object has been created
    # 2 accounting transaction / line
    # 3 allocation supply / line / cell
    # 5 assignment request
    # 1 compute node
    # 2 credential request
    # 2 event
    # 1 instance tree
    # 6 open sale order / line
    # 5 (can reduce to 2) assignment
    # 10 simulation mvt
    # 3 packing list / line
    # 3 sale supply / line
    # 3 sale trade condition
    # 1 software installation
    # 1 software instance
    # 1 software product
    # 1 subscription change request
    # 4 subscription requests
    self.assertRelatedObjectCount(project, 54)

    self.checkERP5StateBeforeExit()
