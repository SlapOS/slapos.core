# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2022 Nexedi SA and Contributors. All Rights Reserved.
#
##############################################################################

from erp5.component.test.testSlapOSERP5VirtualMasterScenario import TestSlapOSVirtualMasterScenarioMixin
from erp5.component.test.SlapOSTestCaseMixin import PinnedDateTime
from DateTime import DateTime
from erp5.component.module.DateUtils import addToDate


class TestSlapOSAccountingScenario(TestSlapOSVirtualMasterScenarioMixin):

  def test_notPaidOpenOrderScenario(self):
    """
    User does not pay the subscription, which is cancelled after some time
    """
    with PinnedDateTime(self, DateTime('2023/05/19')):
      owner_person, _, project = self.bootstrapAccountingTest()
    # Ensure no unexpected object has been created
    # 2 assignment
    # 2 sale supply + line
    # 2 sale trade condition
    # 1 subscription requests
    self.assertRelatedObjectCount(project, 7)

    self.assertFalse(owner_person.Entity_hasOutstandingAmount(include_planned=True))
    self.assertFalse(owner_person.Entity_hasOutstandingAmount())
    self.assertEqual(project.getValidationState(), "validated")
    subscription_request = self.portal.portal_catalog.getResultValue(
      portal_type="Subscription Request",
      aggregate__uid=project.getUid()
    )
    self.assertEqual(subscription_request.getSimulationState(), "submitted")
    deposit_outstanding_amount_list = owner_person.Entity_getOutstandingDepositAmountList()
    self.assertEqual(len(deposit_outstanding_amount_list), 1)
    self.assertEqual(subscription_request.getUid(),
     deposit_outstanding_amount_list[0].getUid())
    
    with PinnedDateTime(self, DateTime('2024/04/04')):
      payment_transaction = owner_person.Entity_createDepositPaymentTransaction(
        deposit_outstanding_amount_list)
      # payzen interface will only stop the payment
      payment_transaction.stop()
      self.tic()

    self.assertTrue(owner_person.Entity_hasOutstandingAmount(include_planned=True))
    amount_list = owner_person.Entity_getOutstandingAmountList(include_planned=True)
    self.assertEqual(len(amount_list), 1)
    self.assertAlmostEqual(amount_list[0].total_price, 24.192)
    self.assertFalse(owner_person.Entity_hasOutstandingAmount())
    self.assertEqual(subscription_request.getSimulationState(), "invalidated")
    open_sale_order = self.portal.portal_catalog.getResultValue(
      portal_type="Open Sale Order Line",
      aggregate__uid=project.getUid()
    ).getParentValue()
    self.assertEqual(open_sale_order.getValidationState(), "validated")
    # invoice is the same month's day of the person creation
    # So, the open order period before '2024/04/03' starts on '2024/03/19'
    self.assertEqual(open_sale_order.getStartDate(), DateTime('2024/03/19'))
    self.assertEqual(open_sale_order.getStartDate(),
                     open_sale_order.getStopDate())
    first_invoice = self.portal.portal_catalog.getResultValue(
      portal_type="Invoice Line",
      aggregate__uid=project.getUid()
    ).getParentValue()
    self.assertEqual(first_invoice.getUid(), amount_list[0].payment_request_uid)
    self.assertEqual(first_invoice.getSimulationState(), "confirmed")
    self.assertEqual(first_invoice.getStartDate(), DateTime('2024/03/19'))
    self.assertEqual(first_invoice.getStopDate(), DateTime('2024/04/19'))
    # Discount and first subscription
    self.assertAlmostEqual(first_invoice.getTotalPrice(), 24.192)
    # Ensure no unexpected object has been created
    # 1 accounting transaction
    # 1 open order
    # 2 assignment
    # 2 simulation movements
    # 2 sale supply + line
    # 1 sale packing list
    # 2 sale trade condition
    # 1 subscription requests
    self.assertRelatedObjectCount(project, 12)

    with PinnedDateTime(self, DateTime('2024/07/05')):
      self.portal.portal_alarms.update_open_order_simulation.activeSense()
      self.tic()

    self.assertTrue(owner_person.Entity_hasOutstandingAmount(include_planned=True))
    amount_list = owner_person.Entity_getOutstandingAmountList(include_planned=True)
    self.assertEqual(len(amount_list), 1)
    self.assertAlmostEqual(amount_list[0].total_price, 175.392)
    self.assertTrue(owner_person.Entity_hasOutstandingAmount())
    amount_list = owner_person.Entity_getOutstandingAmountList()
    self.assertEqual(len(amount_list), 1)
    self.assertAlmostEqual(amount_list[0].total_price, 124.992)
    self.assertEqual(first_invoice.getSimulationState(), "stopped")
    # Ensure no unexpected object has been created
    # 4 accounting transactions
    # 1 open order
    # 2 assignment
    # 8 simulation movements
    # 2 sale supply + line
    # 4 sale packing list
    # 2 sale trade condition
    # 1 subscription requests
    self.assertRelatedObjectCount(project, 24)

    # Try to pay previous period
    with PinnedDateTime(self, DateTime('2024/07/06')):

      payment_transaction = owner_person.Entity_createPaymentTransaction(
        owner_person.Entity_getOutstandingAmountList(
          at_date=DateTime('2024/05/06'),
          section_uid=first_invoice.getSourceSectionUid(),
          resource_uid=first_invoice.getPriceCurrencyUid(),
          ledger_uid=first_invoice.getLedgerUid(),
          group_by_node=False
        )
      )
      payment_transaction.stop()
      self.assertAlmostEqual(payment_transaction.AccountingTransaction_getTotalCredit(), 74.592)
      self.tic()
      self.assertTrue(owner_person.Entity_hasOutstandingAmount(include_planned=True))
      amount_list = owner_person.Entity_getOutstandingAmountList(include_planned=True)
      self.assertEqual(len(amount_list), 1)
      self.assertEqual(amount_list[0].total_price, 100.8)
      self.assertTrue(owner_person.Entity_hasOutstandingAmount())
      amount_list = owner_person.Entity_getOutstandingAmountList()
      self.assertEqual(len(amount_list), 1)
      self.assertEqual(amount_list[0].total_price, 50.4)
      self.assertTrue(first_invoice.SaleInvoiceTransaction_isLettered())
      # Ensure no unexpected object has been created
      self.assertRelatedObjectCount(project, 24)

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
      self.assertEqual(payment_transaction.AccountingTransaction_getTotalCredit(), 50.4)
      self.tic()
      self.assertTrue(owner_person.Entity_hasOutstandingAmount(include_planned=True))
      amount_list = owner_person.Entity_getOutstandingAmountList(include_planned=True)
      self.assertEqual(len(amount_list), 1)
      self.assertEqual(amount_list[0].total_price, 50.4)
      self.assertFalse(owner_person.Entity_hasOutstandingAmount())
      amount_list = owner_person.Entity_getOutstandingAmountList()
      self.assertEqual(len(amount_list), 0)
      # Ensure no unexpected object has been created
      self.assertRelatedObjectCount(project, 24)

    with PinnedDateTime(self, DateTime('2024/07/06')):
      self.checkERP5StateBeforeExit()


  def test_aggregationOfMonthlyInvoiceScenario(self):
    """
    Generate many different open order
    Try to ensure monthly invoices are correctly created
    """
    creation_date = DateTime('2023/05/19')
    with PinnedDateTime(self, creation_date):
      owner_person, currency, project = self.bootstrapAccountingTest()
      # Create software product
      software_release_url = self.generateNewSoftwareReleaseUrl()
      software_type = 'public type'
      software_product, _, _ = self.addSoftwareProduct(
        "instance product", project, software_release_url, software_type
      )
      # Create supply to buy services
      self.tic()
      sale_supply = self.portal.portal_catalog.getResultValue(
        portal_type='Sale Supply',
        source_project__uid=project.getUid()
      )
      sale_supply.searchFolder(
        portal_type='Sale Supply Line',
        resource__relative_url="service_module/slapos_compute_node_subscription"
      )[0].edit(base_price=7)
      sale_supply.newContent(
        portal_type="Sale Supply Line",
        base_price=6,
        resource_value=software_product
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
        # Just add some large sum, so instances dont get blocked.
        tmp_subscription_request = self.portal.portal_trash.newContent(
          portal_type='Subscription Request',
          temp_object=True,
          start_date=DateTime(),
          # source_section rely on default trade condition, like the rest.
          destination_value=person,
          destination_section_value=person,
          ledger_value=self.portal.portal_categories.ledger.automated,
          price_currency=currency.getRelativeUrl(),
          total_price=99 * 10
        )
    
        payment_transaction = person.Entity_createDepositPaymentTransaction(
          [tmp_subscription_request])
        # payzen interface will only stop the payment
        payment_transaction.stop()
        self.tic()

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
      self.assertEqual(self.portal.portal_catalog.countResults(
        portal_type='Compute Node',
        follow_up__uid=project.getUid()
      )[0][0], 0)
      # Execute activities for all services
      # To try detection bad activity tag dependencies
      self.tic()
      # 1 invoice for the compute node
      # per user:
      # 1 monthly invoice for products
      self.assertEqual(self.portal.portal_catalog.countResults(
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
      self.assertEqual(self.portal.portal_catalog.countResults(
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
      self.assertEqual(self.portal.portal_catalog.countResults(
        portal_type='Sale Invoice Transaction',
        source_project__uid=project.getUid()
      )[0][0], (1 + len(person_list)) * 3)

    with PinnedDateTime(self, creation_date + 5):
      self.checkERP5StateBeforeExit()

  def test_vatFranceToWorldScenario(self):
    """
    Check that VAT rules are applied by default
    """
    creation_date = DateTime('2023/02/19')
    with PinnedDateTime(self, creation_date):
      owner_person, _, project = self.bootstrapAccountingTest()
      owner_person.edit(default_address_region='america/south/brazil')

    # Ensure no unexpected object has been created
    # 2 assignment
    # 2 sale supply + line
    # 2 sale trade condition
    # 1 subscription requests
    self.assertRelatedObjectCount(project, 7)

    ##################################################
    # Add deposit (0.1 to prevent discount generation)
    deposit_outstanding_amount_list = owner_person.Entity_getOutstandingDepositAmountList()
    self.assertEqual(len(deposit_outstanding_amount_list), 1)
    self.assertEqual(sum([i.total_price for i in deposit_outstanding_amount_list]), 42)

    with PinnedDateTime(self, creation_date + 0.1):
      payment_transaction = owner_person.Entity_createDepositPaymentTransaction(
        deposit_outstanding_amount_list)
      # payzen interface will only stop the payment
      payment_transaction.stop()
      self.tic()

      self.logout()
      self.login()
      # Execute activities for all services
      # To try detection bad activity tag dependencies
      self.tic()
      invoice = self.portal.portal_catalog.getResultValue(
        portal_type='Sale Invoice Transaction',
        destination__uid=owner_person.getUid(),
        simulation_state='confirmed'
      )
      tax_line = self.portal.portal_catalog.getResultValue(
        portal_type='Invoice Line',
        parent_uid=invoice.getUid(),
        resource__uid=self.portal.service_module.slapos_tax.getUid()
      )
      self.assertEqual(tax_line.getPrice(), 0)
      self.assertEqual(invoice.getTotalPrice(), 42)

    with PinnedDateTime(self, creation_date + 35):
      self.portal.portal_alarms.update_open_order_simulation.activeSense()
      self.tic()

      self.assertEqual(invoice.getTotalPrice(), 42)
      self.assertEqual(invoice.getSimulationState(), 'stopped')

      # Ensure no unexpected object has been created
      # 2 invoice lines
      # 1 open order
      # 2 assignment
      # 4 simulation movements
      # 2 sale supply + line
      # 2 sale packing lists
      # 2 sale trade condition
      # 1 subscription requests
      self.assertRelatedObjectCount(project, 16)

      self.checkERP5StateBeforeExit()

  def test_depositUsageScenario(self):
    """
    User does not pay the invoice.
    Accountant totally pays it with part of the deposit
    """
    creation_date = DateTime('2024/03/19')
    with PinnedDateTime(self, creation_date):
      owner_person, _, project = self.bootstrapAccountingTest()
    # Ensure no unexpected object has been created
    # 2 assignment
    # 2 sale supply + line
    # 2 sale trade condition
    # 1 subscription requests
    self.assertRelatedObjectCount(project, 7)

    self.assertFalse(owner_person.Entity_hasOutstandingAmount(include_planned=True))
    self.assertFalse(owner_person.Entity_hasOutstandingAmount())
    self.assertEqual(project.getValidationState(), "validated")
    subscription_request = self.portal.portal_catalog.getResultValue(
      portal_type="Subscription Request",
      aggregate__uid=project.getUid()
    )
    self.assertEqual(subscription_request.getSimulationState(), "submitted")
    deposit_outstanding_amount_list = owner_person.Entity_getOutstandingDepositAmountList()
    self.assertEqual(len(deposit_outstanding_amount_list), 1)
    self.assertEqual(subscription_request.getUid(),
     deposit_outstanding_amount_list[0].getUid())

    with PinnedDateTime(self, addToDate(creation_date, to_add={'day': 16})):
      payment_transaction = owner_person.Entity_createDepositPaymentTransaction(
        deposit_outstanding_amount_list)
      # payzen interface will only stop the payment
      payment_transaction.stop()
      self.tic()

    self.assertTrue(owner_person.Entity_hasOutstandingAmount(include_planned=True))
    amount_list = owner_person.Entity_getOutstandingAmountList(include_planned=True)
    self.assertEqual(len(amount_list), 1)
    self.assertAlmostEqual(amount_list[0].total_price, 24.192)
    self.assertFalse(owner_person.Entity_hasOutstandingAmount())
    self.assertEqual(subscription_request.getSimulationState(), "invalidated")
    open_sale_order = self.portal.portal_catalog.getResultValue(
      portal_type="Open Sale Order Line",
      aggregate__uid=project.getUid()
    ).getParentValue()
    self.assertEqual(open_sale_order.getValidationState(), "validated")
    # invoice is the same month's day of the person creation
    # So, the open order period before '2025/04/03' starts on '2025/03/19'
    self.assertEqual(open_sale_order.getStartDate(), creation_date)
    self.assertEqual(open_sale_order.getStartDate(),
                     open_sale_order.getStopDate())
    first_invoice = self.portal.portal_catalog.getResultValue(
      portal_type="Invoice Line",
      aggregate__uid=project.getUid()
    ).getParentValue()
    self.assertEqual(first_invoice.getUid(), amount_list[0].payment_request_uid)
    self.assertEqual(first_invoice.getSimulationState(), "confirmed")
    self.assertEqual(first_invoice.getStartDate(), creation_date)
    self.assertEqual(first_invoice.getStopDate(),
                     addToDate(creation_date, to_add={'month': 1}))
    # Discount and first subscription
    self.assertAlmostEqual(first_invoice.getTotalPrice(), 24.192)
    # Ensure no unexpected object has been created
    # 1 accounting transaction
    # 1 open order
    # 2 assignment
    # 2 simulation movements
    # 2 sale supply + line
    # 1 sale packing list
    # 2 sale trade condition
    # 1 subscription requests
    self.assertRelatedObjectCount(project, 12)

    with PinnedDateTime(self, addToDate(creation_date, to_add={'day': 17})):
      # invalidate the product, in order to stop the subscription
      project.invalidate()
      self.tic()

    self.portal.portal_alarms.slapos_stop_confirmed_aggregated_sale_invoice_transaction.activeSense()
    self.tic()

    self.assertTrue(owner_person.Entity_hasOutstandingAmount(include_planned=True))
    amount_list = owner_person.Entity_getOutstandingAmountList(include_planned=True)
    self.assertEqual(len(amount_list), 1)
    self.assertAlmostEqual(amount_list[0].total_price, 24.192)
    self.assertTrue(owner_person.Entity_hasOutstandingAmount())
    amount_list = owner_person.Entity_getOutstandingAmountList()
    self.assertEqual(len(amount_list), 1)
    self.assertAlmostEqual(amount_list[0].total_price, 24.192)
    self.assertEqual(first_invoice.getSimulationState(), "stopped")
    # Ensure no unexpected object has been created
    # 1 accounting transactions
    # 1 open order
    # 2 assignment
    # 2 simulation movements
    # 2 sale supply + line
    # 1 sale packing list
    # 2 sale trade condition
    # 1 subscription requests
    self.assertRelatedObjectCount(project, 12)

    # Use the deposit to pay the invoice
    accounting_transaction = owner_person.Entity_createAccountingTransactionToConsumeDeposit(
      owner_person.Entity_getOutstandingAmountList(
        #at_date=DateTime('2024/05/06'),
        section_uid=first_invoice.getSourceSectionUid(),
        resource_uid=first_invoice.getPriceCurrencyUid(),
        ledger_uid=first_invoice.getLedgerUid(),
        group_by_node=False
      )
    )
    self.assertAlmostEqual(accounting_transaction.AccountingTransaction_getTotalCredit(), 42)
    self.tic()

    self.assertFalse(owner_person.Entity_hasOutstandingAmount(include_planned=True))
    amount_list = owner_person.Entity_getOutstandingAmountList(include_planned=True)
    self.assertEqual(len(amount_list), 0)
    self.assertFalse(owner_person.Entity_hasOutstandingAmount())
    amount_list = owner_person.Entity_getOutstandingAmountList()
    self.assertEqual(len(amount_list), 0)
    self.assertTrue(first_invoice.SaleInvoiceTransaction_isLettered())
    # deposit has been consumed
    for line in payment_transaction.getCausalityValue(portal_type='Sale Invoice Transaction')\
                                   .contentValues(portal_type='Accounting Transaction Line'):
      self.assertTrue(line.hasGroupingReference(), line.getRelativeUrl())
    # Ensure no unexpected object has been created
    self.assertRelatedObjectCount(project, 12)
    # Check remaining deposit (42 - 24.192)
    self.assertAlmostEqual(owner_person.Entity_getDepositBalanceAmount([subscription_request]), 17.808)

    with PinnedDateTime(self, addToDate(creation_date, to_add={'day': 17})):
      self.checkERP5StateBeforeExit()

  def test_creditNoteScenario(self):
    """
    User does not pay the invoice.
    Accountant partially pay it with the deposit, and generate the credit note
    to cancel the remaining part of the invoice
    """
    creation_date = DateTime('2024/03/19')
    with PinnedDateTime(self, creation_date):
      owner_person, _, project = self.bootstrapAccountingTest()
    # Ensure no unexpected object has been created
    # 2 assignment
    # 2 sale supply + line
    # 2 sale trade condition
    # 1 subscription requests
    self.assertRelatedObjectCount(project, 7)

    self.assertFalse(owner_person.Entity_hasOutstandingAmount(include_planned=True))
    self.assertFalse(owner_person.Entity_hasOutstandingAmount())
    self.assertEqual(project.getValidationState(), "validated")
    subscription_request = self.portal.portal_catalog.getResultValue(
      portal_type="Subscription Request",
      aggregate__uid=project.getUid()
    )
    self.assertEqual(subscription_request.getSimulationState(), "submitted")
    deposit_outstanding_amount_list = owner_person.Entity_getOutstandingDepositAmountList()
    self.assertEqual(len(deposit_outstanding_amount_list), 1)
    self.assertEqual(subscription_request.getUid(),
     deposit_outstanding_amount_list[0].getUid())

    with PinnedDateTime(self, creation_date + 1):
      payment_transaction = owner_person.Entity_createDepositPaymentTransaction(
        deposit_outstanding_amount_list)
      # payzen interface will only stop the payment
      payment_transaction.stop()
      self.tic()

    self.assertTrue(owner_person.Entity_hasOutstandingAmount(include_planned=True))
    amount_list = owner_person.Entity_getOutstandingAmountList(include_planned=True)
    self.assertEqual(len(amount_list), 1)
    self.assertAlmostEqual(amount_list[0].total_price, 48.888)
    self.assertFalse(owner_person.Entity_hasOutstandingAmount())
    self.assertEqual(subscription_request.getSimulationState(), "invalidated")
    open_sale_order = self.portal.portal_catalog.getResultValue(
      portal_type="Open Sale Order Line",
      aggregate__uid=project.getUid()
    ).getParentValue()
    self.assertEqual(open_sale_order.getValidationState(), "validated")
    # invoice is the same month's day of the person creation
    # So, the open order period before '2025/04/03' starts on '2025/03/19'
    self.assertEqual(open_sale_order.getStartDate(), creation_date)
    self.assertEqual(open_sale_order.getStartDate(),
                     open_sale_order.getStopDate())
    first_invoice = self.portal.portal_catalog.getResultValue(
      portal_type="Invoice Line",
      aggregate__uid=project.getUid()
    ).getParentValue()
    self.assertEqual(first_invoice.getUid(), amount_list[0].payment_request_uid)
    self.assertEqual(first_invoice.getSimulationState(), "confirmed")
    self.assertEqual(first_invoice.getStartDate(), creation_date)
    self.assertEqual(first_invoice.getStopDate(),
                     addToDate(creation_date, to_add={'month': 1}))
    # Discount and first subscription
    self.assertAlmostEqual(first_invoice.getTotalPrice(), 48.888)
    # Ensure no unexpected object has been created
    # 1 accounting transaction
    # 1 open order
    # 2 assignment
    # 2 simulation movements
    # 2 sale supply + line
    # 1 sale packing list
    # 2 sale trade condition
    # 1 subscription requests
    self.assertRelatedObjectCount(project, 12)

    with PinnedDateTime(self, addToDate(creation_date, to_add={'day': 16})):
      # invalidate the product, in order to stop the subscription
      project.invalidate()
      self.tic()

    self.portal.portal_alarms.slapos_stop_confirmed_aggregated_sale_invoice_transaction.activeSense()
    self.tic()

    self.assertTrue(owner_person.Entity_hasOutstandingAmount(include_planned=True))
    amount_list = owner_person.Entity_getOutstandingAmountList(include_planned=True)
    self.assertEqual(len(amount_list), 1)
    self.assertAlmostEqual(amount_list[0].total_price, 48.888)
    self.assertTrue(owner_person.Entity_hasOutstandingAmount())
    amount_list = owner_person.Entity_getOutstandingAmountList()
    self.assertEqual(len(amount_list), 1)
    self.assertAlmostEqual(amount_list[0].total_price, 48.888)
    self.assertEqual(first_invoice.getSimulationState(), "stopped")
    # Ensure no unexpected object has been created
    # 1 accounting transactions
    # 1 open order
    # 2 assignment
    # 2 simulation movements
    # 2 sale supply + line
    # 1 sale packing list
    # 2 sale trade condition
    # 1 subscription requests
    self.assertRelatedObjectCount(project, 12)

    # Use the deposit to pay the invoice
    payment_transaction = owner_person.Entity_createAccountingTransactionToConsumeDeposit(
      owner_person.Entity_getOutstandingAmountList(
        #at_date=DateTime('2024/05/06'),
        section_uid=first_invoice.getSourceSectionUid(),
        resource_uid=first_invoice.getPriceCurrencyUid(),
        ledger_uid=first_invoice.getLedgerUid(),
        group_by_node=False,
      ),
      create_credit_note=True
    )
    self.assertAlmostEqual(payment_transaction.AccountingTransaction_getTotalCredit(), 42)
    self.tic()

    self.assertFalse(owner_person.Entity_hasOutstandingAmount(include_planned=True))
    amount_list = owner_person.Entity_getOutstandingAmountList(include_planned=True)
    self.assertEqual(len(amount_list), 0)
    self.assertFalse(owner_person.Entity_hasOutstandingAmount())
    amount_list = owner_person.Entity_getOutstandingAmountList()
    self.assertEqual(len(amount_list), 0)
    self.assertTrue(first_invoice.SaleInvoiceTransaction_isLettered())
    # deposit has been consumed
    for line in payment_transaction.getCausalityValue(portal_type='Sale Invoice Transaction')\
                                   .contentValues(portal_type='Accounting Transaction Line'):
      self.assertTrue(line.hasGroupingReference(), line.getRelativeUrl())
    # One partial mirror transaction has been created
    self.assertRelatedObjectCount(project, 13)
    # Check remaining deposit
    self.assertAlmostEqual(owner_person.Entity_getDepositBalanceAmount([subscription_request]), 0)

    with PinnedDateTime(self, addToDate(creation_date, to_add={'day': 16})):
      self.checkERP5StateBeforeExit()