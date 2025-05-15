# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2022 Nexedi SA and Contributors. All Rights Reserved.
#
##############################################################################

from erp5.component.test.testSlapOSERP5VirtualMasterScenario import TestSlapOSVirtualMasterScenarioMixin
from erp5.component.test.SlapOSTestCaseMixin import PinnedDateTime
from DateTime import DateTime
import pkg_resources

class TestSlapOSConsumptionScenarioMixin(TestSlapOSVirtualMasterScenarioMixin):

  def addConsumptionService(self):
    # Create a new service to sell.
    service_new_id = self.generateNewId()
    consumption_service = self.portal.service_module.newContent(
      title="Resource for Consumption %s" % service_new_id,
      reference='IRESOURCEFORCONSUMPTION-%s' % service_new_id,
      quantity_unit='unit/piece',  # Probaly wrong
      base_contribution=[
        'base_amount/invoicing/discounted',
        'base_amount/invoicing/taxable',
      ],
      use='trade/consumption',
      product_line='cloud/usage'
    )
    self.assertEqual(consumption_service.checkConsistency(), [])
    consumption_service.validate()
    return consumption_service


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
    consumption_service = self.addConsumptionService()
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
    sale_supply.newContent(
      portal_type="Sale Supply Line",
      base_price=7,
      resource_value=consumption_service
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
             consumption_service, type_variation

class TestSlapOSConsumptionScenario(TestSlapOSConsumptionScenarioMixin):

  def test_compute_node_consumption_scenario(self):
    with PinnedDateTime(self, DateTime('2024/12/17')):
      project, _, owner_person, project_owner_person, public_server, _, \
        public_server_software, _, consumption_service, \
        _ = self.bootstrapConsumptionScenarioTest()

      self.login()
      self.tic()

    with PinnedDateTime(self, DateTime('2024/12/18')):
      # This alarms is called every day, so it is ok to invoke this here.
      # and not for via interaction workflows
      self.stepCallSlaposAccountingCreateHostingSubscriptionSimulationAlarm()
      self.tic()

    # No instance is created, since we would like to charge for the computer
    # itself.
    with PinnedDateTime(self, DateTime('2025/01/18  01:00')):
      # Minimazed version of the original file, only with a sub-set of values
      # that matter
      consumption_xml_report = """<?xml version="1.0" encoding="utf-8"?>
<journal>
  <transaction type="Sale Packing List">
    <title>Eco Information for %(compute_node_reference)s </title>
    <start_date>2025-01-17 00:00:00</start_date>
    <stop_date>2025-01-17 23:59:59</stop_date>
    <reference>2025-01-17-global</reference>
    <currency/>
    <payment_mode/>
    <category/>
    <arrow type="Destination"/>
    <movement>
      <resource>%(service_reference)s</resource>
      <title>%(service_title)s</title>
      <reference>%(compute_node_reference)s</reference>
      <quantity>27.266539196940727</quantity>
      <price>0.0</price>
      <VAT/>
      <category/>
    </movement>
  </transaction>
</journal>""" % ({
        'compute_node_reference': public_server.getReference(),
        'service_reference': consumption_service.getReference(),
        'service_title': consumption_service.getTitle()})

      compute_node_consumption_model = \
        pkg_resources.resource_string(
          'slapos.slap',
          'doc/computer_consumption.xsd')

      # Ensure what is written above is valid
      self.assertTrue(self.portal.portal_slap._validateXML(
        consumption_xml_report, compute_node_consumption_model))

      # Simulate computer upload
      self.simulateSlapgridUR(public_server, consumption_xml_report)
      self.tic()

      consumption_report_list = public_server.getContributorRelatedValueList()
      self.assertEqual(len(consumption_report_list), 1)
      consumption_report = consumption_report_list[0]
      self.assertEqual(consumption_report.getReference(),
                'TIOCONS-%s-2025-01-17-global' % public_server.getReference())

      self.assertEqual(consumption_report.getValidationState(), "accepted")
      # This alarms is called every day, so it is ok to invoke this here.
      # and not for via interaction workflows
      self.stepCallSlaposAccountingCreateHostingSubscriptionSimulationAlarm()

      self.tic()
      # and uninstall some software on them
      self.logout()
      self.login(owner_person.getUserId())
      self.supplySoftware(public_server,
                          public_server_software,
                          state='destroyed')

      self.logout()
      # Uninstall from compute_node
      self.login()
      self.simulateSlapgridSR(public_server)
      self.tic()

    # Recheck for computer owner if he has consumption invoices
    transaction_list = self.portal.account_module.receivable.Account_getAccountingTransactionList(
      mirror_section_uid=project_owner_person.getUid())

    self.assertEqual(len(transaction_list),  4)
    self.assertSameSet(
      [round(x.total_price, 2) for x in transaction_list],
      [50.4, 347.84, 141.0, -141.0],
      [round(x.total_price, 2) for x in transaction_list],
    )

    self.login()

    # Ensure no unexpected object has been created
    # 2 accounting transaction / line
    # 3 allocation supply / line / cell
    # 1 compute node
    # 1 consumption delivery
    # 1 consumption deocument
    # 1 credential request
    # 1 event
    # 3 open sale order / line
    # 4 assignment
    # 16 simulation mvt
    # 2 packing list / line
    # 4 sale supply / line
    # 2 sale trade condition
    # 1 software installation
    # 1 software product
    # 2 subscription requests
    self.assertRelatedObjectCount(project, 45)

    self.checkERP5StateBeforeExit()

  def test_instance_tree_consumption_scenario(self):
    with PinnedDateTime(self, DateTime('2024/12/17')):
      project, currency, owner_person, _, public_server, public_instance_type, \
        public_server_software, software_product, consumption_service, \
        type_variation = self.bootstrapConsumptionScenarioTest()

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

      # Minimazed version of the original file, only with a sub-set of values
      # that matter
      consumption_xml_report = """<?xml version="1.0" encoding="utf-8"?>
<journal>
  <transaction type="Sale Packing List">
    <title>Eco Information for %(compute_node_reference)s </title>
    <start_date>2025-01-17 00:00:00</start_date>
    <stop_date>2025-01-17 23:59:59</stop_date>
    <reference>2025-01-17-global</reference>
    <currency/>
    <payment_mode/>
    <category/>
    <arrow type="Destination"/>
    <movement>
      <resource>%(service_reference)s</resource>
      <title>%(service_title)s</title>
      <reference>%(software_instance_reference)s</reference>
      <quantity>29</quantity>
      <price>0.0</price>
      <VAT/>
      <category/>
    </movement>
    <movement>
      <resource>%(service_reference)s</resource>
      <title>%(service_title)s</title>
      <reference>%(software_instance_reference2)s</reference>
      <quantity>29</quantity>
      <price>0.0</price>
      <VAT/>
      <category/>
    </movement>
  </transaction>
</journal>""" % ({
        'software_instance_reference': software_instance.getReference(),
        'software_instance_reference2': software_instance2.getReference(),
        'compute_node_reference': public_server.getReference(),
        'service_reference': consumption_service.getReference(),
        'service_title': consumption_service.getTitle()})

      compute_node_consumption_model = \
        pkg_resources.resource_string(
          'slapos.slap',
          'doc/computer_consumption.xsd')

      # Ensure what is written above is valid
      self.assertTrue(self.portal.portal_slap._validateXML(
        consumption_xml_report, compute_node_consumption_model))

      # Simulate computer upload
      self.simulateSlapgridUR(public_server, consumption_xml_report)
      self.tic()

      consumption_report_list = public_server.getContributorRelatedValueList()
      self.assertEqual(len(consumption_report_list), 1)
      consumption_report = consumption_report_list[0]
      self.assertEqual(consumption_report.getReference(),
                'TIOCONS-%s-2025-01-17-global' % public_server.getReference())
      self.assertEqual(consumption_report.getValidationState(), "accepted")

    with PinnedDateTime(self, DateTime('2025/01/19 01:00')):
      self.login()
      # Next day remote more consumption
      consumption_xml_report = """<?xml version="1.0" encoding="utf-8"?>
<journal>
  <transaction type="Sale Packing List">
    <title>Eco Information for %(compute_node_reference)s </title>
    <start_date>2025-01-18 00:00:00</start_date>
    <stop_date>2025-01-18 23:59:59</stop_date>
    <reference>2025-01-18-global</reference>
    <currency/>
    <payment_mode/>
    <category/>
    <arrow type="Destination"/>
    <movement>
      <resource>%(service_reference)s</resource>
      <title>%(service_title)s</title>
      <reference>%(software_instance_reference)s</reference>
      <quantity>23</quantity>
      <price>0.0</price>
      <VAT/>
      <category/>
    </movement>
    <movement>
      <resource>%(service_reference)s</resource>
      <title>%(service_title)s</title>
      <reference>%(software_instance_reference2)s</reference>
      <quantity>23</quantity>
      <price>0.0</price>
      <VAT/>
      <category/>
    </movement>
  </transaction>
</journal>""" % ({
        'software_instance_reference': software_instance.getReference(),
        'software_instance_reference2': software_instance2.getReference(),
        'compute_node_reference': public_server.getReference(),
        'service_reference': consumption_service.getReference(),
        'service_title': consumption_service.getTitle()})

      compute_node_consumption_model = \
        pkg_resources.resource_string(
          'slapos.slap',
          'doc/computer_consumption.xsd')

      # Ensure what is written above is valid
      self.assertTrue(self.portal.portal_slap._validateXML(
        consumption_xml_report, compute_node_consumption_model))

      # Simulate computer upload
      self.simulateSlapgridUR(public_server, consumption_xml_report)
      self.tic()

      consumption_report_list = public_server.getContributorRelatedValueList()
      self.assertEqual(len(consumption_report_list), 2)
      consumption_report = [i for i in consumption_report_list \
          if "2025-01-18" in i.getReference()][0]

      self.assertEqual(consumption_report.getReference(),
                'TIOCONS-%s-2025-01-18-global' % public_server.getReference())

      self.assertEqual(consumption_report.getValidationState(), "accepted")

      self.login(owner_person.getUserId())
      # Unallocate and destroy the instance the instances
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

    # Was 10.8 correspond to the first month since it passed a month by the
    # dates.
    self.assertEqual(len(transaction_list), 5)
    self.assertSameSet(
      [round(x.total_price, 2) for x in transaction_list],
      [9.0, -9.0, round(508.8, 2), -10.8, 10.8],
      [round(x.total_price, 2) for x in transaction_list]
    )

    self.login()

    # Ensure no unexpected object has been created
    # 4 accounting transaction / line
    # 3 allocation supply / line / cell
    # 1 compute node
    # 2 consumption delivery
    # 2 consumption document
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
    self.assertRelatedObjectCount(project, 118)

    self.checkERP5StateBeforeExit()

  def test_sparse_instance_tree_consumption_scenario(self):
    """ Split into multiple reports """
    with PinnedDateTime(self, DateTime('2024/12/17')):
      project, currency, owner_person, _, public_server, public_instance_type, \
        public_server_software, software_product, consumption_service, \
        type_variation = self.bootstrapConsumptionScenarioTest()

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

    # Create the first daily report
    with PinnedDateTime(self, DateTime('2025/01/18 01:00')):
      self.login()

      # Search used partition
      instance_tree = self.portal.portal_catalog.getResultValue(
        title=public_instance_title, portal_type='Instance Tree',
        default_destination_section_uid=public_person.getUid())

      self.assertNotEqual(None, instance_tree)
      software_instance = instance_tree.getSuccessorValue()
      partition = software_instance.getAggregateValue()
      self.assertEqual(partition.getParentValue(), public_server)

      # Minimazed version of the original file, only with a sub-set of values
      # that matter
      consumption_xml_report = """<?xml version="1.0" encoding="utf-8"?>
<journal>
  <transaction type="Sale Packing List">
    <title>Test Consumption file for %(compute_node_reference)s </title>
    <start_date>2025-01-17 00:00:00</start_date>
    <stop_date>2025-01-17 23:59:59</stop_date>
    <reference>2025-01-17-global</reference>
    <currency/>
    <payment_mode/>
    <category/>
    <arrow type="Destination"/>
    <movement>
      <resource>%(service_reference)s</resource>
      <title>%(service_title)s</title>
      <reference>%(software_instance_reference)s</reference>
      <quantity>29.12</quantity>
      <price>0.0</price>
      <VAT/>
      <category/>
    </movement>
  </transaction>
</journal>""" % ({
        'software_instance_reference': software_instance.getReference(),
        'compute_node_reference': public_server.getReference(),
        'service_reference': consumption_service.getReference(),
        'service_title': consumption_service.getTitle()})

      compute_node_consumption_model = \
        pkg_resources.resource_string(
          'slapos.slap',
          'doc/computer_consumption.xsd')

      # Ensure what is written above is valid
      self.assertTrue(self.portal.portal_slap._validateXML(
        consumption_xml_report, compute_node_consumption_model))

      # Simulate computer upload
      self.simulateSlapgridUR(public_server, consumption_xml_report)
      self.tic()

      consumption_report_list = public_server.getContributorRelatedValueList()
      self.assertEqual(len(consumption_report_list), 1)
      consumption_report = consumption_report_list[0]
      self.assertEqual(consumption_report.getReference(),
                'TIOCONS-%s-2025-01-17-global' % public_server.getReference())

      self.assertEqual(consumption_report.getValidationState(), "accepted")

    # Include second report
    with PinnedDateTime(self, DateTime('2025/01/19 01:00')):
      # XXX This could be called by an interaction workflow
      instance_tree2 = self.portal.portal_catalog.getResultValue(
        title=public_instance_title2, portal_type='Instance Tree',
        default_destination_section_uid=public_person.getUid())

      self.assertNotEqual(None, instance_tree2)
      software_instance2 = instance_tree2.getSuccessorValue()
      partition2 = software_instance2.getAggregateValue()
      self.assertEqual(partition2.getParentValue(), public_server)

      # Minimazed version of the original file, only with a sub-set of values
      # that matter
      consumption_xml_report = """<?xml version="1.0" encoding="utf-8"?>
<journal>
  <transaction type="Sale Packing List">
    <title>Test Consumption file for %(compute_node_reference)s </title>
    <start_date>2025-01-18 00:00:00</start_date>
    <stop_date>2025-01-18 23:59:59</stop_date>
    <reference>2025-01-18-global</reference>
    <currency/>
    <payment_mode/>
    <category/>
    <arrow type="Destination"/>
    <movement>
      <resource>%(service_reference)s</resource>
      <title>%(service_title)s</title>
      <reference>%(software_instance_reference2)s</reference>
      <quantity>29.12</quantity>
      <price>0.0</price>
      <VAT/>
      <category/>
    </movement>
  </transaction>
</journal>""" % ({
        'software_instance_reference': software_instance.getReference(),
        'software_instance_reference2': software_instance2.getReference(),
        'compute_node_reference': public_server.getReference(),
        'service_reference': consumption_service.getReference(),
        'service_title': consumption_service.getTitle()})

      # Ensure what is written above is valid
      self.assertTrue(self.portal.portal_slap._validateXML(
        consumption_xml_report, compute_node_consumption_model))

      # Simulate computer upload
      self.simulateSlapgridUR(public_server, consumption_xml_report)
      self.tic()

      consumption_report_list = public_server.getContributorRelatedValueList()
      self.assertEqual(len(consumption_report_list), 2)
      consumption_report = [ i for i in consumption_report_list \
                                         if "2025-01-18" in i.getReference()][0]
      self.assertEqual(consumption_report.getReference(),
                'TIOCONS-%s-2025-01-18-global' % public_server.getReference())

      self.assertEqual(consumption_report.getValidationState(), "accepted")

      self.login(owner_person.getUserId())
      # Unallocate and destroy the instance the instances
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

    # Was 10.8 correspond to the first month since it passed a month by the
    # dates.
    self.assertEqual(len(transaction_list), 5)
    self.assertSameSet(
      [round(x.total_price, 2) for x in transaction_list],
      [round(266.208, 2), 9.0, -9.0, 10.8, -10.8],
      [round(x.total_price, 2) for x in transaction_list]
    )

    self.login()

    # Ensure no unexpected object has been created
    # 4 accounting transaction / line
    # 3 allocation supply / line / cell
    # 1 compute node
    # 2 consumption delivery
    # 2 consumption document
    # 2 credential request
    # 3 event
    # 2 instance tree
    # 9 open sale order / line
    # 5 (can reduce to 2) assignment
    # 51 simulation mvt
    # 6 packing list / line
    # 4 sale supply / line
    # 2 sale trade condition
    # 1 software installation
    # 2 software instance
    # 1 software product
    # 4 subscription requests
    self.assertRelatedObjectCount(project, 104)

    self.checkERP5StateBeforeExit()
