# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2022 Nexedi SA and Contributors. All Rights Reserved.
#
##############################################################################

from erp5.component.test.testSlapOSERP5VirtualMasterScenario import TestSlapOSVirtualMasterScenarioMixin
from erp5.component.test.SlapOSTestCaseMixin import PinnedDateTime, TemporaryAlarmScript
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
                             release_variation, type_variation,
                             is_slave_on_same_instance_tree_allocable=True)


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
             public_instance_type, public_server_software


  def getInvoiceLineOfConsumptionDelivery(self, consumption_delivery):
    rule = consumption_delivery.getCausalityRelatedValue(portal_type='Applied Rule')
    sm = rule.objectValues(portal_type='Simulation Movement')[0].objectValues(portal_type='Applied Rule')[0].objectValues(porta_type='Simulation Movement')[0]
    return sm.getDeliveryValue()

  def test_instance_consumption_scenario_with_different_instance_tree(self):
    with PinnedDateTime(self, DateTime('2024/12/17')):
      project, currency, owner_person, project_owner_person, public_server, public_instance_type, \
        public_server_software  = self.bootstrapConsumptionScenarioTest()

      self.logout()

      # join as the another visitor and request software instance on public
      # compute_node
      public_reference = 'public-%s' % self.generateNewId()
      public_person = self.joinSlapOS(self.web_site, public_reference)

      self.login()

    with PinnedDateTime(self, DateTime('2025/01/17 01:01')):
      # Simulate access from compute_node, to open the capacity scope
      self.login()
      self.simulateSlapgridSR(public_server)

      public_instance_title = 'Public title %s' % self.generateNewId()
      self.checkInstanceAllocationWithDeposit(public_person.getUserId(),
          public_reference, public_instance_title,
          public_server_software, public_instance_type,
          public_server, project.getReference(),
          9.0, currency)
      instance_tree = self.portal.portal_catalog.getResultValue(
        title=public_instance_title, portal_type='Instance Tree',
        default_destination_section_uid=public_person.getUid())
      software_instance = instance_tree.getSuccessorValue()
      consumption_delivery = software_instance.getCausalityRelatedValue(portal_type='Consumption Delivery')
      self.assertTrue(consumption_delivery is not None)


    with PinnedDateTime(self, DateTime('2025/01/17 01:02')):
      public_instance_title2 = 'Public title %s 2' % self.generateNewId()
      self.checkInstanceAllocationWithDeposit(public_person.getUserId(),
          public_reference, public_instance_title2,
          public_server_software, public_instance_type,
          public_server, project.getReference(),
          10.8, currency)
      instance_tree2 = self.portal.portal_catalog.getResultValue(
        title=public_instance_title2, portal_type='Instance Tree',
        default_destination_section_uid=public_person.getUid())

      software_instance2 = instance_tree2.getSuccessorValue()
      consumption_delivery2 = software_instance2.getCausalityRelatedValue(portal_type='Consumption Delivery')
      self.assertTrue(consumption_delivery2 is not None)

    self.tic()
    # generate only one invoice line
    invoice_line = self.getInvoiceLineOfConsumptionDelivery(consumption_delivery)

    self.assertEqual(
      invoice_line,
      self.getInvoiceLineOfConsumptionDelivery(consumption_delivery2)
    )
    invoice = invoice_line.getParentValue()
    self.assertEqual(invoice.getSimulationState(), "confirmed")
    self.assertEqual(invoice.getStartDate(), DateTime('2025/01/17'))
    self.assertEqual(invoice.getStopDate(), DateTime('2025/02/17'))
    self.assertEqual(invoice.getTotalPrice(), 62.4)


    self.assertEqual(invoice_line.getResource(), 'service_module/instance_consumption')
    self.assertEqual(invoice_line.getQuantity(), 2)
    self.assertEqual(invoice_line.getPrice(), 5)
    self.logMessage(project_owner_person.getRelativeUrl())
    amount_list = project_owner_person.Entity_getOutstandingAmountList(include_planned=True)
    self.assertEqual(len(amount_list), 1)
    amount = amount_list[0]
    self.assertEqual(amount.total_price, 350.4)


    payment_transaction = project_owner_person.Entity_createPaymentTransaction(amount_list)
    self.assertAlmostEqual(payment_transaction.AccountingTransaction_getTotalCredit(), 350.4)
    self.tic()

    with PinnedDateTime(self, DateTime('2025/01/17 01:03')):

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
      # Ensure no unexpected object has been created
      # 13 accounting transaction / line
      # 3 allocation supply / line / cell
      # 1 compute node
      # 6 consumption delivery
      # 2 credential request
      # 3 event
      # 2 instance tree
      # 9 open sale order / line
      # 5 (can reduce to 2) assignment
      # 90 simulation mvt
      # 14 packing list / line
      # 4 sale supply / line
      # 2 sale trade condition
      # 1 software installation
      # 2 software instance
      # 1 software product
      # 4 subscription requests
      self.assertRelatedObjectCount(project, 89)

    with PinnedDateTime(self, DateTime('2025/01/17 01:04')):
      self.checkERP5StateBeforeExit()


  def test_instance_consumption_scenario_with_multi_instance_in_one_instance_tree(self):
    with PinnedDateTime(self, DateTime('2024/12/17')):
      project, currency, owner_person, _, public_server, public_instance_type, \
        public_server_software= self.bootstrapConsumptionScenarioTest()

      self.logout()

      # join as the another visitor and request software instance on public
      # compute_node
      public_reference = 'public-%s' % self.generateNewId()
      public_person = self.joinSlapOS(self.web_site, public_reference)

      self.login()

    with PinnedDateTime(self, DateTime('2025/01/17 01:01')):
      # Simulate access from compute_node, to open the capacity scope
      self.login()
      self.simulateSlapgridSR(public_server)

      public_instance_title = 'Public title %s' % self.generateNewId()
      self.checkInstanceAllocationWithDeposit(
        public_person.getUserId(),
        public_reference,
        public_instance_title,
        public_server_software,
        public_instance_type,
        public_server,
        project.getReference(),
        9.0,
        currency)
      self.login(public_person.getUserId())
      slave_instance_title = 'Slave title %s' % self.generateNewId()
      self.checkInstanceTreeSlaveInstanceAllocation(
        public_person.getUserId(),
        public_reference, public_instance_title,
        slave_instance_title,
        public_server_software, public_instance_type,
        public_server, project.getReference()
      )

      self.login()
      self.tic()
      instance_tree = self.portal.portal_catalog.getResultValue(
        title=public_instance_title, portal_type='Instance Tree',
        default_destination_section_uid=public_person.getUid())
      software_instance = instance_tree.getSuccessorValue()
      slave_instance = software_instance.getSuccessorValue()
      consumption_delivery = software_instance.getCausalityRelatedValue(portal_type='Consumption Delivery')
      consumption_delivery2 = slave_instance.getCausalityRelatedValue(portal_type='Consumption Delivery')
      self.assertTrue(consumption_delivery is not None)
      self.assertTrue(consumption_delivery2 is not None)



    with PinnedDateTime(self, DateTime('2025/05/23 01:00')):
      self.login()
      # update open sale order of project
      self.portal.portal_alarms.update_open_order_simulation.activeSense()
      self.tic()
      self.portal.portal_alarms.slapos_accounting_generate_consumption_delivery_for_validated_instance.activeSense()
      self.tic()
      for instance in [software_instance, slave_instance]:
        consumption_delivery_list = instance.getCausalityRelatedValueList(portal_type='Consumption Delivery')
        self.assertEqual(len(consumption_delivery_list), 5)

    with TemporaryAlarmScript(self.portal, 'Base_generateConsumptionDeliveryForInvalidatedInstance'):
      with PinnedDateTime(self, DateTime('2025/07/23 01:00')):
        self.login(owner_person.getUserId())
        self.checkInstanceUnallocation(
          public_person.getUserId(),
          public_reference, public_instance_title,
          public_server_software, public_instance_type, public_server,
          project.getReference()
        )

        self.checkSlaveInstanceUnallocation(
          public_person.getUserId(),
          public_reference,
          slave_instance_title,
          public_server_software,
          public_instance_type,
          public_server,
          project.getReference()
        )


    with PinnedDateTime(self, DateTime('2025/09/23 01:00')):
      self.login()
      self.portal.portal_alarms.slapos_accounting_generate_consumption_delivery_for_invalidated_instance.activeSense()
      self.tic()
      #here we need to check consumption deliveries datas
      for instance in [software_instance, slave_instance]:
        consumption_delivery_list = instance.getCausalityRelatedValueList(portal_type='Consumption Delivery')
        self.assertEqual(len(consumption_delivery_list), 9)
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

    self.login()
    # the lists in comment changes too often, let's updated at the end
    # Ensure no unexpected object has been created
    # 21 accounting transaction / line
    # 3 allocation supply / line / cell
    # 1 compute node
    # 9 consumption delivery
    # 2 credential request
    # 3 event
    # 2 instance tree
    # 6 open sale order / line
    # 5 (can reduce to 2) assignment
    # 121 simulation mvt
    # 19 packing list / line
    # 4 sale supply / line
    # 2 sale trade condition
    # 1 software installation
    # 2 software instance
    # 1 software product
    # 4 subscription requests
    self.assertRelatedObjectCount(project, 230)
    with PinnedDateTime(self, DateTime('2024/07/06')):
      self.checkERP5StateBeforeExit()

  def test_validate_software_instance(self):
    with PinnedDateTime(self,  DateTime('2024/12/17')):
      instance = self.portal.software_instance_module.newContent(portal_type='Software Instance')
      self._test_alarm_not_visited(
        self.portal.portal_alarms.slapos_accounting_generate_consumption_delivery_for_validated_instance,
        instance,
        'Base_generateConsumptionDeliveryForValidatedInstance'
      )

    with PinnedDateTime(self,  DateTime('2024/12/17 01:00')):
      with TemporaryAlarmScript(self.portal, 'Base_generateConsumptionDeliveryForValidatedInstance'):
        instance.validate()
        self.tic()

    self.assertEqual(instance.getExpirationDate(), None)

    with PinnedDateTime(self,  DateTime('2024/12/17 01:01')):
      self._test_alarm(
        self.portal.portal_alarms.slapos_accounting_generate_consumption_delivery_for_validated_instance,
        instance,
        'Base_generateConsumptionDeliveryForValidatedInstance'
      )
      instance.edit()
      self.tic()


    with PinnedDateTime(self,  DateTime('2024/12/17 02:01')):
      self._test_alarm(
        self.portal.portal_alarms.slapos_accounting_generate_consumption_delivery_for_validated_instance,
        instance,
        'Base_generateConsumptionDeliveryForValidatedInstance'
      )
      instance.edit()
      self.tic()

    self.assertEqual(instance.getExpirationDate(), None)
    with PinnedDateTime(self,  DateTime('2024/12/17 03:01')):
      instance.setExpirationDate(DateTime() + 1)
      self._test_alarm_not_visited(
        self.portal.portal_alarms.slapos_accounting_generate_consumption_delivery_for_validated_instance,
        instance,
        'Base_generateConsumptionDeliveryForValidatedInstance'
      )
    self.assertNotEqual(instance.getExpirationDate(), None)

    with PinnedDateTime(self,  DateTime('2024/12/17 03:01') + 1):
      self._test_alarm(
        self.portal.portal_alarms.slapos_accounting_generate_consumption_delivery_for_validated_instance,
        instance,
        'Base_generateConsumptionDeliveryForValidatedInstance'
      )

  def test_invalidated_software_instance(self):

    with PinnedDateTime(self,  DateTime('2024/12/17')):
      instance = self.portal.software_instance_module.newContent(portal_type='Software Instance')
      self.portal.portal_workflow._jumpToStateFor(instance, 'invalidated')
      self.tic()

    with PinnedDateTime(self, DateTime('2024/12/17 01:00')):
      self._test_alarm(
        self.portal.portal_alarms.slapos_accounting_generate_consumption_delivery_for_invalidated_instance,
        instance,
        'Base_generateConsumptionDeliveryForInvalidatedInstance'
      )
      # To clean last edit comment
      instance.edit()
      self.tic()

    self.assertEqual(instance.getExpirationDate(), None)

    with PinnedDateTime(self, DateTime('2024/12/17 02:00')):
      self._test_alarm(
        self.portal.portal_alarms.slapos_accounting_generate_consumption_delivery_for_invalidated_instance,
        instance,
        'Base_generateConsumptionDeliveryForInvalidatedInstance'
      )
      instance.edit(expiration_date = DateTime())
      self.tic()

    with PinnedDateTime(self, DateTime('2024/12/17 03:00')):
      self._test_alarm_not_visited(
        self.portal.portal_alarms.slapos_accounting_generate_consumption_delivery_for_invalidated_instance,
        instance,
        'Base_generateConsumptionDeliveryForInvalidatedInstance'
      )
      instance.edit()
      self.tic()

    with PinnedDateTime(self, DateTime('2024/12/17 04:00')):
      self._test_alarm_not_visited(
        self.portal.portal_alarms.slapos_accounting_generate_consumption_delivery_for_invalidated_instance,
        instance,
        'Base_generateConsumptionDeliveryForInvalidatedInstance'
      )
