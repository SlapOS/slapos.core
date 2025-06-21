# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2022 Nexedi SA and Contributors. All Rights Reserved.
#
##############################################################################

from erp5.component.test.testSlapOSERP5VirtualMasterScenario import TestSlapOSVirtualMasterScenarioMixin
from erp5.component.test.SlapOSTestCaseMixin import PinnedDateTime

from DateTime import DateTime

class testSlapOSConsumptionScenarioForInstance(TestSlapOSVirtualMasterScenarioMixin):


  def bootstrapConsumptionScenarioTest(self):
    currency, _, _, sale_person, _ = self.bootstrapVirtualMasterTest()

    self.logout()
    # lets join as slapos administrator, which will manager the project
    project_owner_reference = 'project-%s' % self.generateNewId()
    project_owner_person = self.joinSlapOS(
      self.web_site, project_owner_reference)

    self.login()
    self.tic()
    self.logout()
    self.login(sale_person.getUserId())

    project_relative_url = self.addProject(
      is_accountable=True,
      person=project_owner_person,
      currency=currency)

    project = self.portal.restrictedTraverse(project_relative_url)
    self.logout()
    self.login()

    preference = self.portal.portal_preferences.slapos_default_system_preference
    preference.edit(
      preferred_subscription_assignment_category_list=[
        'function/customer',
        'role/client',
        'destination_project/%s' % project_relative_url
      ]
    )

    public_server_software = self.generateNewSoftwareReleaseUrl()
    public_instance_type = 'public type'

    software_product, release_variation, type_variation = self.addSoftwareProduct(
      "instance product", project, public_server_software, public_instance_type
    )

    self.tic()

    self.logout()
    self.login(sale_person.getUserId())

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

    # Do like this for now, change later
    sale_supply.newContent(
      portal_type='Sale Supply Line',
      base_price = 5,
      resource_value = self.portal.service_module.instance_consumption
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

    # Pay deposit to validate virtual master + one computer
    deposit_amount = 42.0 + 99.0
    self.login(project_owner_person.getUserId())
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

    return project, currency, owner_person, project_owner_person, public_server, \
             public_instance_type, public_server_software, software_product, \
             type_variation

  def addConsumptionServiceForInstance(self):# No extra parameter for now
    pass

  def test_instance_consumption_scenario(self):
    with PinnedDateTime(self, DateTime('2024/12/17')):
      project, currency, owner_person, _, public_server, public_instance_type, \
        public_server_software, _,  \
        _ = self.bootstrapConsumptionScenarioTest()

      self.logout()

      # join as the another visitor and request software instance on public
      # compute_node
      public_reference = 'public-%s' % self.generateNewId()
      public_person = self.joinSlapOS(self.web_site, public_reference)

      self.login()


    with PinnedDateTime(self, DateTime('2024/12/17 01:01')):
      # Simulate access from compute_node, to open the capacity scope
      self.login()
      self.simulateSlapgridSR(public_server)
      public_instance_title = 'Public title %s' % self.generateNewId()
      self.checkInstanceAllocationWithDeposit(public_person.getUserId(),
          public_reference, public_instance_title,
          public_server_software, public_instance_type,
          public_server, project.getReference(),
          9.0, currency)

    with PinnedDateTime(self, DateTime('2024/12/17 01:02')):
      public_instance_title2 = 'Public title %s 2' % self.generateNewId()
      self.checkInstanceAllocationWithDeposit(public_person.getUserId(),
          public_reference, public_instance_title2,
          public_server_software, public_instance_type,
          public_server, project.getReference(),
          10.8, currency)

    with PinnedDateTime(self, DateTime('2025/01/18 01:00')):
      self.login()

      # Search used partition
      instance_tree = self.portal.portal_catalog.getResultValue(
        title=public_instance_title, portal_type='Instance Tree',
        default_destination_section_uid=public_person.getUid())

      instance_tree2 = self.portal.portal_catalog.getResultValue(
        title=public_instance_title2, portal_type='Instance Tree',
        default_destination_section_uid=public_person.getUid())

      self.assertNotEqual(None, instance_tree)
      software_instance = instance_tree.getSuccessorValue()
      partition = software_instance.getAggregateValue()
      self.assertEqual(partition.getParentValue(), public_server)

      self.assertNotEqual(None, instance_tree2)
      software_instance2 = instance_tree2.getSuccessorValue()
      partition2 = software_instance2.getAggregateValue()
      self.assertEqual(partition2.getParentValue(), public_server)

      consumption_delivery = software_instance.getCausalityRelatedValue(portal_type='Consumption Delivery')
      consumption_delivery2 = software_instance2.getCausalityRelatedValue(portal_type='Consumption Delivery')
      self.assertTrue(consumption_delivery is not None)
      self.assertTrue(consumption_delivery2 is not None)

      self.login(owner_person.getUserId())
      # Unallocate and destroy the instance the instances
      # This unallocate software instance then trigger alarm which will check other software instance also
      # thus create another consumption delivery for software_instance2
      # XXXX this wrong, we should create one consumption delivery for software_instance
      self.checkInstanceUnallocation(public_person.getUserId(),
          public_reference, public_instance_title,
          public_server_software, public_instance_type, public_server,
          project.getReference())

      self.checkInstanceUnallocation(public_person.getUserId(),
          public_reference, public_instance_title2,
          public_server_software, public_instance_type, public_server,
          project.getReference())

      # and uninstall some software on them
      self.logout()
      self.login(owner_person.getUserId())
      self.supplySoftware(public_server,
                          public_server_software,
                          state='destroyed')

      self.logout()
      # Uninstall from compute_node
      self.login()
      self.tic()


    # Check accounting
    transaction_list = self.portal.account_module.receivable.Account_getAccountingTransactionList(
      mirror_section_uid=public_person.getUid())

    # 9    deposite
    # 9    deposite
    # 21.6 instance
    # 10.8 deposite
    # 10.8 deposite
    for transaction in transaction_list:
      self.logMessage(transaction.getRelativeUrl())

    self.assertEqual(len(transaction_list), 5)
    self.assertSameSet(
      [round(x.total_price, 2) for x in transaction_list],
      [9.0, -9.0, 21.6, -10.8, 10.8],
      [round(x.total_price, 2) for x in transaction_list]
    )
    self.assertEqual(
      consumption_delivery.getCausalityRelatedValue(portal_type='Sale Invoice Transaction'),
      consumption_delivery2.getCausalityRelatedValue(portal_type='Sale Invoice Transaction')
    )
    self.login()

    # Ensure no unexpected object has been created
    # 4 accounting transaction / line
    # 3 allocation supply / line / cell
    # 1 compute node
    # 2 consumption delivery
    # 2 consumption document
    # 2 consumption supply
    # 2 credential request
    # 3 event
    # 2 instance tree
    # 9 open sale order / line
    # 5 (can reduce to 2) assignment
    # 65 simulation mvt
    # 6 packing list / line
    # 4 sale supply / line
    # 2 sale trade condition
    # 1 software installation
    # 2 software instance
    # 1 software product
    # 4 subscription requests
    self.assertRelatedObjectCount(project, 113)

    self.checkERP5StateBeforeExit()
