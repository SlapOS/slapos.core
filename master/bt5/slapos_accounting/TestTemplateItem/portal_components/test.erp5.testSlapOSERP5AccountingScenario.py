# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2022 Nexedi SA and Contributors. All Rights Reserved.
#
##############################################################################

from erp5.component.test.testSlapOSERP5VirtualMasterScenario import TestSlapOSVirtualMasterScenarioMixin
from erp5.component.test.SlapOSTestCaseMixin import PinnedDateTime
from DateTime import DateTime


class TestSlapOSAccountingScenario(TestSlapOSVirtualMasterScenarioMixin):

  def bootstrapAccountingTest(self):
    currency, _, _, sale_person = self.bootstrapVirtualMasterTest()
    self.tic()

    self.logout()
    # lets join as slapos administrator, which will manager the project
    owner_reference = 'project-%s' % self.generateNewId()
    self.joinSlapOS(self.web_site, owner_reference)

    self.login()
    owner_person = self.portal.portal_catalog.getResultValue(
      portal_type="ERP5 Login",
      reference=owner_reference).getParentValue()
    self.tic()
    self.logout()

    self.login(sale_person.getUserId())
    with PinnedDateTime(self, DateTime('2020/01/01')):
      project_relative_url = self.addProject(
        is_accountable=True,
        person=owner_person,
        currency=currency
      )
      self.tic()
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
    return owner_person, currency, project

  def test_rejectedSubscriptionScenario(self):
    """
    User does not pay the subscription, which is cancelled after some time
    """
    _, _, project = self.bootstrapAccountingTest()

    self.assertEqual(project.getValidationState(), "invalidated")
    subscription_request = self.portal.portal_catalog.getResultValue(
      portal_type="Subscription Request",
      aggregate__uid=project.getUid()
    )
    self.assertEqual(subscription_request.getSimulationState(), "cancelled")

    # Ensure no unexpected object has been created
    # 2 assignment
    # 2 sale trade condition
    # 1 subscription requests
    self.assertRelatedObjectCount(project, 5)

    self.checkERP5StateBeforeExit()

  def test_notPaidOpenOrderScenario(self):
    """
    User does not pay the subscription, which is cancelled after some time
    """
    with PinnedDateTime(self, DateTime('2020/05/19')):
      owner_person, currency, project = self.bootstrapAccountingTest()
    # Ensure no unexpected object has been created
    # 2 assignment
    # 2 sale trade condition
    # 1 subscription requests
    self.assertRelatedObjectCount(project, 5)

    self.assertFalse(owner_person.Entity_hasOutstandingAmount(include_planned=True))
    self.assertFalse(owner_person.Entity_hasOutstandingAmount())
    self.assertEqual(project.getValidationState(), "validated")
    subscription_request = self.portal.portal_catalog.getResultValue(
      portal_type="Subscription Request",
      aggregate__uid=project.getUid()
    )
    self.assertEqual(subscription_request.getSimulationState(), "submitted")

    with PinnedDateTime(self, DateTime('2021/04/04')):
      payment_transaction = owner_person.Person_addDepositPayment(99*10, currency.getRelativeUrl(), 1)
      payment_transaction.PaymentTransaction_acceptDepositPayment()
      self.tic()

    self.assertTrue(owner_person.Entity_hasOutstandingAmount(include_planned=True))
    amount_list = owner_person.Entity_getOutstandingAmountList(include_planned=True)
    self.assertEquals(len(amount_list), 1)
    self.assertEquals(amount_list[0].total_price, 24.384)
    self.assertFalse(owner_person.Entity_hasOutstandingAmount())
    self.assertEqual(subscription_request.getSimulationState(), "invalidated")
    open_sale_order = self.portal.portal_catalog.getResultValue(
      portal_type="Open Sale Order Line",
      aggregate__uid=project.getUid()
    ).getParentValue()
    self.assertEqual(open_sale_order.getValidationState(), "validated")
    # invoice is the same month's day of the person creation
    # So, the open order period before '2021/04/03' starts on '2021/03/19'
    self.assertEqual(open_sale_order.getStartDate(), DateTime('2021/03/19'))
    self.assertEqual(open_sale_order.getStartDate(),
                     open_sale_order.getStopDate())
    first_invoice = self.portal.portal_catalog.getResultValue(
      portal_type="Invoice Line",
      aggregate__uid=project.getUid()
    ).getParentValue()
    self.assertEqual(first_invoice.getUid(), amount_list[0].payment_request_uid)
    self.assertEqual(first_invoice.getSimulationState(), "confirmed")
    self.assertEqual(first_invoice.getStartDate(), DateTime('2021/03/19'))
    self.assertEqual(first_invoice.getStopDate(), DateTime('2021/04/19'))
    # Discount and first subscription
    self.assertEqual(first_invoice.getTotalPrice(), 24.384)
    # Ensure no unexpected object has been created
    # 1 accounting transaction
    # 1 open order
    # 2 assignment
    # 2 simulation movements
    # 1 sale packing list
    # 2 sale trade condition
    # 1 subscription requests
    self.assertRelatedObjectCount(project, 10)

    with PinnedDateTime(self, DateTime('2021/07/05')):
      self.portal.portal_alarms.update_open_order_simulation.activeSense()
      self.tic()

    self.assertTrue(owner_person.Entity_hasOutstandingAmount(include_planned=True))
    amount_list = owner_person.Entity_getOutstandingAmountList(include_planned=True)
    self.assertEquals(len(amount_list), 1)
    self.assertEquals(amount_list[0].total_price, 175.584)
    self.assertTrue(owner_person.Entity_hasOutstandingAmount())
    amount_list = owner_person.Entity_getOutstandingAmountList()
    self.assertEquals(len(amount_list), 1)
    self.assertEquals(amount_list[0].total_price, 125.184)
    self.assertEqual(first_invoice.getSimulationState(), "stopped")
    # Ensure no unexpected object has been created
    # 4 accounting transactions
    # 1 open order
    # 2 assignment
    # 8 simulation movements
    # 4 sale packing list
    # 2 sale trade condition
    # 1 subscription requests
    self.assertRelatedObjectCount(project, 22)

    # Try to pay previous period
    with PinnedDateTime(self, DateTime('2021/07/06')):

      payment_transaction = owner_person.Entity_createPaymentTransaction(
        owner_person.Entity_getOutstandingAmountList(
          at_date=DateTime('2021/05/06'),
          section_uid=first_invoice.getSourceSectionUid(),
          resource_uid=first_invoice.getPriceCurrencyUid(),
          ledger_uid=first_invoice.getLedgerUid(),
          group_by_node=False
        )
      )
      payment_transaction.stop()
      self.assertEquals(payment_transaction.AccountingTransaction_getTotalCredit(), 74.78399999999999)
      self.tic()
      self.assertTrue(owner_person.Entity_hasOutstandingAmount(include_planned=True))
      amount_list = owner_person.Entity_getOutstandingAmountList(include_planned=True)
      self.assertEquals(len(amount_list), 1)
      self.assertEquals(amount_list[0].total_price, 100.8)
      self.assertTrue(owner_person.Entity_hasOutstandingAmount())
      amount_list = owner_person.Entity_getOutstandingAmountList()
      self.assertEquals(len(amount_list), 1)
      self.assertEquals(amount_list[0].total_price, 50.4)
      self.assertTrue(first_invoice.SaleInvoiceTransaction_isLettered())
      # Ensure no unexpected object has been created
      self.assertRelatedObjectCount(project, 22)

      payment_tag = "Entity_createPaymentTransaction_%s" % owner_person.getUid()
      owner_person.REQUEST.set(payment_tag, None)

      payment_transaction = owner_person.Entity_createPaymentTransaction(
        owner_person.Entity_getOutstandingAmountList(
          section_uid=first_invoice.getSourceSectionUid(),
          resource_uid=first_invoice.getPriceCurrencyUid(),
          ledger_uid=first_invoice.getLedgerUid(),
          group_by_node=False
        )
      )
      payment_transaction.stop()
      self.assertEquals(payment_transaction.AccountingTransaction_getTotalCredit(), 50.4)
      self.tic()
      self.assertTrue(owner_person.Entity_hasOutstandingAmount(include_planned=True))
      amount_list = owner_person.Entity_getOutstandingAmountList(include_planned=True)
      self.assertEquals(len(amount_list), 1)
      self.assertEquals(amount_list[0].total_price, 50.4)
      self.assertFalse(owner_person.Entity_hasOutstandingAmount())
      amount_list = owner_person.Entity_getOutstandingAmountList()
      self.assertEquals(len(amount_list), 0)
      # Ensure no unexpected object has been created
      self.assertRelatedObjectCount(project, 22)

    with PinnedDateTime(self, DateTime('2021/07/06')):
      self.checkERP5StateBeforeExit()

  def createProductionManager(self, project):
    production_manager_reference = 'production_manager-%s' % self.generateNewId()
    self.joinSlapOS(self.web_site, production_manager_reference)

    self.login()
    production_manager_person = self.portal.portal_catalog.getResultValue(
      portal_type="ERP5 Login",
      reference=production_manager_reference).getParentValue()

    self.addProjectProductionManagerAssignment(production_manager_person, project)
    self.tic()
    return production_manager_person

  def test_aggregationOfMonthlyInvoiceScenario(self):
    """
    Generate many different open order
    Try to ensure monthly invoices are correctly created
    couscous
    """
    creation_date = DateTime('2020/05/19')
    with PinnedDateTime(self, creation_date):
      owner_person, currency, project = self.bootstrapAccountingTest()
      # Create software product
      software_release_url = self.generateNewSoftwareReleaseUrl()
      software_type = 'public type'
      software_product, _, _ = self.addSoftwareProduct(
        "instance product", project, software_release_url, software_type
      )
      # Create supply to buy services
      sale_supply = self.portal.sale_supply_module.newContent(
        portal_type="Sale Supply",
        title="price for %s" % project.getRelativeUrl(),
        source_project_value=project,
        price_currency_value=currency
      )
      sale_supply.newContent(
        portal_type="Sale Supply Line",
        base_price=6,
        resource_value=software_product
      )
      sale_supply.newContent(
        portal_type="Sale Supply Line",
        base_price=7,
        resource="service_module/slapos_compute_node_subscription"
      )
      sale_supply.validate()
      self.tic()
    # Ensure no unexpected object has been created
    # 2 assignment
    # 2 sale trade condition
    # 1 subscription requests
    # 1 software product
    # 3 sale supply + lines
    self.assertRelatedObjectCount(project, 9)

    ##################################################
    # Create other users
    # Same creation date
    with PinnedDateTime(self, creation_date):
      same_creation_date_user = self.createProductionManager(project)
    # Different creation date
    with PinnedDateTime(self, creation_date + 1):
      different_creation_date_user = self.createProductionManager(project)

    person_list = [owner_person, same_creation_date_user,
                   different_creation_date_user]
    ##################################################
    # Add deposit
    with PinnedDateTime(self, creation_date + 2):
      for person in person_list:
        payment_transaction = person.Person_addDepositPayment(99*100, currency.getRelativeUrl(), 1)
        payment_transaction.PaymentTransaction_acceptDepositPayment()

    ##################################################
    # Add first batch of service, and generate invoices
    # Use a different date, to ensure discount are also created
    with PinnedDateTime(self, creation_date + 3):
      for person in person_list:
        self.logout()
        self.login(person.getUserId())
        self.portal.portal_slap.requestComputer(self.generateNewId(),
                                                project.getReference())
    with PinnedDateTime(self, creation_date + 3):
      for person in person_list:
        self.logout()
        self.login(person.getUserId())
        self.portal.portal_slap.requestComputer(self.generateNewId(),
                                                project.getReference())
        self.portal.portal_slap.requestComputerPartition(
          software_release=software_release_url,
          software_type=software_type,
          partition_reference=self.generateNewId(),
          shared_xml='<marshal><bool>0</bool></marshal>',
          project_reference=project.getReference())

      self.logout()
      self.login()
      # Check that no activity has been triggered yet
      self.assertEquals(self.portal.portal_catalog.countResults(
        portal_type='Compute Node',
        follow_up__uid=project.getUid()
      )[0][0], 0)
      # Execute activities for all services
      # To try detection bad activity tag dependencies
      self.tic()
      # 1 invoice for the compute node
      # per user:
      # 1 monthly invoice for products
      self.assertEquals(self.portal.portal_catalog.countResults(
        portal_type='Sale Invoice Transaction',
        source_project__uid=project.getUid()
      )[0][0], 1 + len(person_list))

    ##################################################
    # Add new batch of service, which must be aggregated on the
    # existing invoices
    with PinnedDateTime(self, creation_date + 4):
      for person in person_list:
        self.logout()
        self.login(person.getUserId())
        self.portal.portal_slap.requestComputer(self.generateNewId(),
                                                project.getReference())
        self.portal.portal_slap.requestComputerPartition(
          software_release=software_release_url,
          software_type=software_type,
          partition_reference=self.generateNewId(),
          shared_xml='<marshal><bool>0</bool></marshal>',
          project_reference=project.getReference())
      self.logout()
      self.login()
      # Execute activities for all services
      # To try detection bad activity tag dependencies
      self.tic()
      self.assertEquals(self.portal.portal_catalog.countResults(
        portal_type='Sale Invoice Transaction',
        source_project__uid=project.getUid()
      )[0][0], 1 + len(person_list))

    ##################################################
    # Ensure new monthly invoices are created
    with PinnedDateTime(self, creation_date + 80):
      self.logout()
      self.login()
      self.portal.portal_alarms.update_open_order_simulation.activeSense()
      self.tic()
      self.assertEquals(self.portal.portal_catalog.countResults(
        portal_type='Sale Invoice Transaction',
        source_project__uid=project.getUid()
      )[0][0], (1 + len(person_list)) * 3)

    with PinnedDateTime(self, creation_date + 5):
      self.checkERP5StateBeforeExit()