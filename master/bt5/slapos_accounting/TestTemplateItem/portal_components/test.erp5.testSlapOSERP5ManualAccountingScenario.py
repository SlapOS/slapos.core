# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2024 Nexedi SA and Contributors. All Rights Reserved.
#
##############################################################################

from erp5.component.test.testSlapOSERP5VirtualMasterScenario import TestSlapOSVirtualMasterScenarioMixin
from erp5.component.test.SlapOSTestCaseMixin import PinnedDateTime
from DateTime import DateTime


class TestSlapOSManualAccountingScenarioMixin(TestSlapOSVirtualMasterScenarioMixin):
  def bootstrapManualAccountingTest(self):
    currency, _, _, sale_person, _ = self.bootstrapVirtualMasterTest()
    self.tic()

    self.logout()
    # lets join as slapos administrator, which will manager the project
    accountant_reference = 'accountant-%s' % self.generateNewId()
    accountant_person = self.joinSlapOS(self.web_site, accountant_reference)

    self.tic()
    self.login(sale_person.getUserId())
    self.addAccountingManagerAssignment(accountant_person)

    self.tic()
    self.logout()

    self.login(accountant_person.getUserId())

    accountant_organisation = self.portal.organisation_module.newContent(
      portal_type="Organisation",
      title="test-accountant-%s" % self.generateNewId(),
      # required to generate accounting report
      price_currency_value=currency,
      # required to calculate the vat
      default_address_region='europe/west/france'
    )
    bank_account = accountant_organisation.newContent(
      portal_type="Bank Account",
      title="test_bank_account_%s" % self.generateNewId(),
      price_currency_value=currency
    )

    bank_account.validate()
    accountant_organisation.validate()

    return accountant_person, accountant_organisation, \
      bank_account, currency

  def createBalanceForOrganisation(self, accountant, organisation, transaction_list):

    # Group is required and should be unique, else the Balance will
    # generate/cover way too much.
    self.login()
    group = self.portal.portal_categories.group.newContent(
      id='test_group_%s' % self.generateNewId(),
      title="Group for %s" % organisation.getTitle()
    )

    self.logout()
    self.login(accountant.getUserId())
    organisation.setGroup(group.getId())

    # Create Accounting Period and start
    year = DateTime().strftime("%Y")
    accounting_period = organisation.newContent(
      portal_type="Accounting Period",
      title=year,
      start_date=DateTime("%s/01/01" % year),
      stop_date=DateTime("%s/12/31" % year)
    )

    self.portal.portal_workflow.doActionFor(accounting_period, "start_action")
    self.tic()
    # Close all transactions before close the period.
    for transaction in transaction_list:
      self.portal.portal_workflow.doActionFor(transaction, "deliver_action")
    self.tic()

    self.portal.portal_workflow.doActionFor(accounting_period, "stop_action",
      profit_and_loss_account="account_module/profit_loss")
    self.tic()

    balance_transaction_list = self.portal.portal_catalog(
      portal_type='Balance Transaction',
      destination_section_uid=organisation.getUid(),
      simulation_state='delivered'
    )
    self.assertEqual(len(balance_transaction_list), 1)
    balance_transaction = balance_transaction_list[0].getObject()

    self.assertEqual(balance_transaction.getCausality(),
                     accounting_period.getRelativeUrl())

    self.assertEqual(balance_transaction.getResource(),
                     organisation.getPriceCurrency())

    self.assertEqual(
      balance_transaction.getStopDate(),
      DateTime("%s/01/01" % (int(DateTime().strftime("%Y")) + 1))
    )
    self.assertEqual(
      balance_transaction.getDestinationReference(),
      "%s-1" % (int(DateTime().strftime("%Y")) + 1)
    )

    return balance_transaction

  def groupAndAssertLineList(self, entity, line_list):
    # Emulate the Grouping fast input
    grouped_line_list = entity.AccountingTransaction_guessGroupedLines(
      accounting_transaction_line_uid_list=[i.getUid() for i in line_list])

    self.assertNotEqual(grouped_line_list, None)
    self.assertEqual(len(grouped_line_list), len(line_list))

    expected_reference = line_list[0].getGroupingReference()
    expected_date = line_list[0].getGroupingDate()
    
    for line in line_list:
      self.assertNotEqual(line.getGroupingReference(), None)
      self.assertEqual(line.getGroupingReference(), expected_reference)
      self.assertNotEqual(line.getGroupingDate(), None)
      self.assertEqual(line.getGroupingDate(), expected_date)

  def stopAndAssertTransaction(self, transaction):
    # Ensure consistency
    self.assertEqual(transaction.checkConsistency(), [])
    # Post to general ledger
    self.portal.portal_workflow.doActionFor(transaction, 'stop_action')
    self.tic()
    self.assertEqual(transaction.getSimulationState(), 'stopped')


class TestSlapOSManualAccountingScenario(TestSlapOSManualAccountingScenarioMixin):

  def test_purchase_invoice_transaction(self, provider_as_organisation=False):
    """
    Accountant creates a Purchase Invoice Transaction and group it with a
    Payment Transaction.
    """
    with PinnedDateTime(self, DateTime('2020/05/19')):
      accountant_person, accountant_organisation, bank_account, currency = \
        self.bootstrapManualAccountingTest()
    
    self.login(accountant_person.getUserId())

    # Accountant can create one account for Hosting
    account = self.portal.account_module.newContent(
      portal_type='Account',
      reference='626000',
      title='Hosting for %s' % accountant_person.getTitle(),
      account_type='expense',
      financial_section='expense',
      gap_list=['ias/ifrs/6/60/600', 'fr/pcg/6/62/626']
    )
    account.validate()

    if provider_as_organisation:
      # Accountaint can create a hosting provider
      provider = self.portal.organisation_module.newContent(
        portal_type='Organisation',
        title='Service Provider for %s' % accountant_person.getTitle(),
      )
    else:
      provider = self.portal.person_module.newContent(
        portal_type='Person',
        title='Service Provider for %s' % accountant_person.getTitle())

    # Create a simple Purchase Invoice Transaction
    transaction = self.portal.accounting_module.newContent(
      title='Purchase for %s' % accountant_person.getTitle(),
      portal_type="Purchase Invoice Transaction",
      # Dates are required for rset source/destination reference
      start_date=DateTime() - 1,
      stop_date=DateTime() - 1,
      resource_value=currency,
      source_section_value=provider,
      destination_section_value=accountant_organisation
    )

    total_amount = 9876.30
    tax_amount = total_amount * 0.12
    transaction.newContent(
      portal_type='Purchase Invoice Transaction Line',
      quantity=total_amount - tax_amount,
      destination=account.getRelativeUrl()
    )
    transaction.newContent(
      portal_type='Purchase Invoice Transaction Line',
      quantity=tax_amount,
      destination='account_module/refundable_vat'
    )
    purchase_payable_line = transaction.newContent(
      portal_type='Purchase Invoice Transaction Line',
      quantity=-total_amount,  # Negative value
      destination='account_module/payable'
    )

    self.tic()
    self.stopAndAssertTransaction(transaction)
    
    # Time to pay
    payment = self.portal.accounting_module.newContent(
      title='Payment for %s' % accountant_person.getTitle(),
      portal_type="Payment Transaction",
      # Dates are required for rset source/destination reference
      start_date=DateTime(),
      stop_date=DateTime(),
      resource_value=currency,
      source_section_value=accountant_organisation,
      destination_section_value=provider,
      source_payment_value=bank_account
    )

    self.tic()

    # Initial payment has 3 lines by default.
    self.assertEqual(len(payment.objectValues()), 3, payment.getRelativeUrl())
    # for testing sake, we re-add payble later
    payment.manage_delObjects(ids=['receivable', 'payable'])
    payment.bank.edit(
      source="account_module/bank",
      quantity=total_amount
    )

    payable_line = payment.newContent(
      portal_type='Accounting Transaction Line',
      quantity=-total_amount,
      source="account_module/payable"
    )
    self.tic()
    self.stopAndAssertTransaction(payment)

    # No automatic grouping until here
    self.assertEqual(payable_line.getGroupingReference(), None)

    self.groupAndAssertLineList(
      provider, [payable_line, purchase_payable_line])

    balance_transaction = self.createBalanceForOrganisation(
      accountant_person, accountant_organisation, [payment, transaction])
    
    line_list = balance_transaction.contentValues(portal_types="Balance Transaction Line")
    self.assertEqual(len(line_list), 3)

    profit_loss_list = [line for line in line_list if line.getDestination() == 'account_module/profit_loss']
    self.assertEqual(len(profit_loss_list), 1)
    profit_loss = profit_loss_list[0]
    self.assertEqual(profit_loss.getQuantity(), 8691.14)

    bank_list = [line for line in line_list if line.getDestination() == 'account_module/bank']
    self.assertEqual(len(bank_list), 1)
    bank_line = bank_list[0]
    self.assertEqual(bank_line.getQuantity(), -9876.3)
    self.assertEqual(bank_line.getDestinationPayment(), bank_account.getRelativeUrl())

    tax_list = [line for line in line_list if line.getDestination() == 'account_module/refundable_vat']
    self.assertEqual(len(tax_list), 1)
    tax_line = tax_list[0]
    self.assertEqual(tax_line.getQuantity(), 1185.16)

  def test_purchase_invoice_transaction_organisation(self):
    self.test_purchase_invoice_transaction(provider_as_organisation=False)

  def test_accounting_transaction(self, customer_as_organisation=False):
    """ Basic scenario for accountant create an Accounting transaction
        to rembourse a customer (person by default)
    """
    with PinnedDateTime(self, DateTime('2020/05/19')):
      accountant_person, accountant_organisation, bank_account, currency = \
        self.bootstrapManualAccountingTest()
    
    self.login(accountant_person.getUserId())

    # Accountant can create one account for Remboursement of a customer
    account = self.portal.account_module.newContent(
      portal_type='Account',
      reference='628000',
      title='Remboursement for %s' % accountant_person.getTitle(),
      account_type='expense',
      financial_section='expense',
      gap_list=['ias/ifrs/6/60/600', 'fr/pcg/6/62/628']
    )
    account.validate()

    if not customer_as_organisation:
      customer = self.portal.organisation_module.newContent(
        portal_type='Organisation',
        title='Customer for remboursement for %s' % accountant_person.getTitle()
      )
    else:
      customer = self.portal.person_module.newContent(
        portal_type='Person',
        title='Customer for remboursement for %s' % accountant_person.getTitle()
      )

    # Create a simple Accounting Transaction
    transaction = self.portal.accounting_module.newContent(
      title='Remboursement for %s' % accountant_person.getTitle(),
      portal_type="Accounting Transaction",
      # Dates are required for rset source/destination reference
      start_date=DateTime() - 1,
      stop_date=DateTime() - 1,
      resource_value=currency,
      source_section_value=customer,
      destination_section_value=accountant_organisation
    )

    total_amount = 100.30
    transaction.newContent(
      portal_type='Accounting Transaction Line',
      quantity=total_amount,
      destination=account.getRelativeUrl()
    )
    accounting_payable_line = transaction.newContent(
      portal_type='Accounting Transaction Line',
      quantity=-total_amount,  # Negative value
      destination='account_module/payable'
    )

    self.tic()
    self.stopAndAssertTransaction(transaction)

    # Time to pay
    payment = self.portal.accounting_module.newContent(
      title='Payment Rembourse for %s' % accountant_person.getTitle(),
      portal_type="Payment Transaction",
      # Dates are required for set source/destination reference
      start_date=DateTime(),
      stop_date=DateTime(),
      resource_value=currency,
      source_section_value=accountant_organisation,
      destination_section_value=customer,
      source_payment_value=bank_account
    )

    self.tic()
    # Initial payment has 3 lines by default.
    self.assertEqual(len(payment.objectValues()), 3, payment.getRelativeUrl())
    # for testing sake, we re-add payble later
    payment.manage_delObjects(ids=['receivable', 'payable'])
    payment.bank.edit(
      source="account_module/bank",
      quantity=total_amount
    )
    payable_line = payment.newContent(
      portal_type='Accounting Transaction Line',
      quantity=-total_amount,
      source="account_module/payable"
    )
    self.tic()
    self.stopAndAssertTransaction(payment)

    # No automatic grouping until here
    self.assertEqual(payable_line.getGroupingReference(), None)

    self.groupAndAssertLineList(
      customer, [payable_line, accounting_payable_line])

    balance_transaction = self.createBalanceForOrganisation(
      accountant_person, accountant_organisation, [payment, transaction])

    line_list = balance_transaction.contentValues(portal_types="Balance Transaction Line")
    self.assertEqual(len(line_list), 2)

    profit_loss_list = [line for line in line_list if line.getDestination() == 'account_module/profit_loss']
    self.assertEqual(len(profit_loss_list), 1)
    profit_loss = profit_loss_list[0]
    self.assertEqual(profit_loss.getQuantity(), 100.30)

    bank_list = [line for line in line_list if line.getDestination() == 'account_module/bank']
    self.assertEqual(len(bank_list), 1)
    bank_line = bank_list[0]
    self.assertEqual(bank_line.getQuantity(), -100.30)
    self.assertEqual(bank_line.getDestinationPayment(), bank_account.getRelativeUrl())



  def test_accounting_transaction_organisation(self):
    """ Basic scenario for accountant create an Accounting transaction
        to rembourse a customer (organisation)
    """
    return self.test_accounting_transaction(customer_as_organisation=True)

  def test_sale_invoice_transaction(self, customer_as_organisation=False):
    """ Basic scenario for accountant create an Sale invoice transaction
        to sell services for a customer (person by default)
    """
    with PinnedDateTime(self, DateTime('2020/05/19')):
      accountant_person, accountant_organisation, bank_account, currency = \
        self.bootstrapManualAccountingTest()


    # Accountant can create one account for Remboursement of a customer
    account = self.portal.account_module.newContent(
      portal_type='Account',
      reference='628000',
      title='Service Provisioning for %s' % accountant_person.getTitle(),
      account_type='income',
      financial_section='income',
      gap_list=['ias/ifrs/7/70', 'fr/pcg/7/70/706']
    )
    account.validate()

    if customer_as_organisation:
      # Accountaint can create a hosting provider
      customer = self.portal.organisation_module.newContent(
        portal_type='Organisation',
        title='Customer Org. for %s' % accountant_person.getTitle()
      )
    else:
      customer = self.portal.person_module.newContent(
        portal_type='Person',
        title='Customer Person for %s' % accountant_person.getTitle(),
        default_address_region='europe/west/france')

    # Create a simple Accounting Transaction
    transaction = self.portal.accounting_module.newContent(
      title='Service Provisioning for %s' % accountant_person.getTitle(),
      portal_type="Sale Invoice Transaction",
      # Dates are required for rset source/destination reference
      start_date=DateTime() - 1,
      stop_date=DateTime() - 1,
      resource_value=currency,
      price_currency_value=currency,
      destination_section_value=customer,
      source_section_value=accountant_organisation
    )

    total_amount = 9876.30
    tax_amount = total_amount * 0.12
    transaction.income.edit(
      quantity=total_amount - tax_amount,
      source=account.getRelativeUrl()
    )
    transaction.collected_vat.edit(
      quantity=tax_amount,
      source='account_module/coll_vat'
    )
    transaction.receivable.edit(
      quantity=-total_amount,  # Negative value
      source='account_module/receivable'
    )
    self.tic()
    self.stopAndAssertTransaction(transaction)

    # Time to pay
    payment = self.portal.accounting_module.newContent(
      title='Payment for %s' % accountant_person.getTitle(),
      portal_type="Payment Transaction",
      # Dates are required for set source/destination reference
      start_date=DateTime(),
      stop_date=DateTime(),
      resource_value=currency,
      source_section_value=accountant_organisation,
      destination_section_value=customer,
      source_payment_value=bank_account
    )

    self.tic()
    # Initial payment has 3 lines by default.
    self.assertEqual(len(payment.objectValues()), 3, payment.getRelativeUrl())
    # for testing sake, we re-add payble later
    payment.manage_delObjects(ids=['receivable', 'payable'])
    payment.bank.edit(
      source="account_module/bank",
      quantity=-total_amount
    )
    receivable_line = payment.newContent(
      portal_type='Accounting Transaction Line',
      quantity=total_amount,
      source="account_module/receivable"
    )
    self.tic()
    self.stopAndAssertTransaction(payment)

    # No automatic grouping until here
    self.assertEqual(receivable_line.getGroupingReference(), None)

    self.groupAndAssertLineList(
      customer, [receivable_line, transaction.receivable])

    balance_transaction = self.createBalanceForOrganisation(
      accountant_person, accountant_organisation, [payment, transaction])

    line_list = balance_transaction.contentValues(portal_types="Balance Transaction Line")
    self.assertEqual(len(line_list), 3)

    profit_loss_list = [line for line in line_list if line.getDestination() == 'account_module/profit_loss']
    self.assertEqual(len(profit_loss_list), 1)
    profit_loss = profit_loss_list[0]
    self.assertEqual(profit_loss.getQuantity(), -8691.14)

    bank_list = [line for line in line_list if line.getDestination() == 'account_module/bank']
    self.assertEqual(len(bank_list), 1)
    bank_line = bank_list[0]
    self.assertEqual(bank_line.getQuantity(), 9876.30)
    self.assertEqual(bank_line.getDestinationPayment(), bank_account.getRelativeUrl())

    tax_list = [line for line in line_list if line.getDestination() == 'account_module/coll_vat']
    self.assertEqual(len(tax_list), 1)
    tax_line = tax_list[0]
    self.assertEqual(tax_line.getQuantity(), -1185.16)


  def test_sale_invoice_transaction_organisation(self):
    """ Basic scenario for accountant create an Sale invoice transaction
        to sell services for a customer (Organisation)
    """
    self.test_sale_invoice_transaction(customer_as_organisation=True)


