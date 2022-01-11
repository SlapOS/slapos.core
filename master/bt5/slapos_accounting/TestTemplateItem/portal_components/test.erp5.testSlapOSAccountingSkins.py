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

from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixin, withAbort

from zExceptions import Unauthorized
from DateTime import DateTime

class TestSlapOSAccounting(SlapOSTestCaseMixin):

  def createHostingSubscription(self):
    new_id = self.generateNewId()
    return self.portal.hosting_subscription_module.newContent(
      portal_type='Hosting Subscription',
      title="Subscription %s" % new_id,
      reference="TESTHS-%s" % new_id,
      )

  def createInstanceTree(self):
    new_id = self.generateNewId()
    return self.portal.instance_tree_module.newContent(
      portal_type='Instance Tree',
      title="Subscription %s" % new_id,
      reference="TESTIT-%s" % new_id,
      )

  def createOpenSaleOrder(self):
    new_id = self.generateNewId()
    return self.portal.open_sale_order_module.newContent(
      portal_type='Open Sale Order',
      title="OpenSaleOrder %s" % new_id,
      reference="TESTOSO-%s" % new_id,
      )

  def createSaleInvoiceTransactionForReversal(self, destination_section=None, price=2, payment_mode="payzen"):
    new_title = self.generateNewId()
    new_reference = self.generateNewId()
    new_source_reference = self.generateNewId()
    new_destination_reference = self.generateNewId()
    invoice = self.portal.accounting_module.newContent(
      portal_type="Sale Invoice Transaction",
      title=new_title,
      start_date=DateTime(),
      reference=new_reference,
      source_reference=new_source_reference,
      destination_reference=new_destination_reference,
      destination_section=destination_section,
      payment_mode=payment_mode,
      ledger='automated',
      specialise="sale_trade_condition_module/slapos_aggregated_trade_condition",
      created_by_builder=1 # to prevent init script to create lines
    )
    self.portal.portal_workflow._jumpToStateFor(invoice, 'stopped')
    invoice.newContent(
      title="",
      portal_type="Invoice Line",
      quantity=-2,
      price=price,
    )
    invoice.newContent(
      portal_type="Sale Invoice Transaction Line",
      source="account_module/receivable",
      quantity=-3,
    )
    return invoice

  #################################################################
  # SaleInvoiceTransaction_createReversalSaleInvoiceTransaction
  #################################################################
  def test_SaleInvoiceTransaction_createReversalSaleInvoiceTransaction_redirect_payzen(self):
    sale_invoice_transaction = self.createSaleInvoiceTransactionForReversal(payment_mode='payzen')
    self.tic()

    redirect = sale_invoice_transaction.SaleInvoiceTransaction_createReversalSaleInvoiceTransaction()
    self.assertTrue(
      redirect.endswith(
        '?portal_status_message=Reversal%20Transaction%20created.'), 
        "%s doesn't end with expected response" % redirect)

  def test_SaleInvoiceTransaction_createReversalSaleInvoiceTransaction_redirect_wechat(self):
    sale_invoice_transaction = self.createSaleInvoiceTransactionForReversal(payment_mode='wechat')
    self.tic()

    redirect = sale_invoice_transaction.SaleInvoiceTransaction_createReversalSaleInvoiceTransaction()
    self.assertTrue(
      redirect.endswith(
        '?portal_status_message=Reversal%20Transaction%20created.'), 
        "%s doesn't end with expected response" % redirect)

  def test_SaleInvoiceTransaction_createReversalSaleInvoiceTransaction_redirect_unknown(self):
    sale_invoice_transaction = self.portal.accounting_module.newContent(portal_type="Sale Invoice Transaction")
    sale_invoice_transaction.edit(payment_mode="unknown")

    redirect = sale_invoice_transaction.SaleInvoiceTransaction_createReversalSaleInvoiceTransaction()

    self.assertTrue(
      redirect.endswith(
        '%s?portal_status_message=The%%20payment%%20mode%%20is%%20unsupported.' % sale_invoice_transaction.getRelativeUrl()), 
      "%s doesn't end with %s?portal_status_message=The%%20payment%%20mode%%20is%%20unsupported." % (
        redirect, sale_invoice_transaction.getRelativeUrl()))

  #################################################################
  # SaleInvoiceTransaction_resetPaymentMode
  #################################################################
  def test_SaleInvoiceTransaction_resetPaymentMode(self):
    sale_invoice_transaction = self.portal.accounting_module.newContent(portal_type="Sale Invoice Transaction")
    sale_invoice_transaction.edit(payment_mode="unknown",
      start_date=DateTime(),
      stop_date=DateTime())
    sale_invoice_transaction.confirm()
    sale_invoice_transaction.start( )
    sale_invoice_transaction.stop()

    sale_invoice_transaction.SaleInvoiceTransaction_resetPaymentMode()
    self.assertEqual(sale_invoice_transaction.getPaymentMode(), "unknown")
    sale_invoice_transaction.edit(payment_mode="payzen")

    sale_invoice_transaction.SaleInvoiceTransaction_resetPaymentMode()
    self.assertEqual(sale_invoice_transaction.getPaymentMode(), None)
    sale_invoice_transaction.edit(payment_mode="wechat")

    sale_invoice_transaction.SaleInvoiceTransaction_resetPaymentMode()
    self.assertEqual(sale_invoice_transaction.getPaymentMode(), None)

    self.assertRaises(
      Unauthorized,
      sale_invoice_transaction.SaleInvoiceTransaction_resetPaymentMode,
      REQUEST={})

  #################################################################
  # AccountingTransactionModule_getUnpaidInvoiceList
  #################################################################
  def test_AccountingTransactionModule_getUnpaidInvoiceList(self):
    project = self.addProject()
    person = self.makePerson(project, user=1)
    organisation = self.portal.organisation_module.newContent(
      portal_type="Organisation"
    )
    sale_trade_condition = self.portal.sale_trade_condition_module.newContent(
      portal_type="Sale Trade Condition",
      reference=self.generateNewId(),
      specialise="business_process_module/slapos_ultimate_business_process"
    )
    sale_trade_condition.validate()

    current_invoice = self.portal.accounting_module.newContent(
      portal_type="Sale Invoice Transaction",
      created_by_builder=1,# to prevent init script to create lines
      specialise_value=sale_trade_condition,
      source_section_value=organisation,
      destination_value=person,
      destination_section_value=person,
      destination_decision_value=person,
      start_date=DateTime('2019/10/20'),
      stop_date=DateTime('2019/10/20'),
      title='Fake Invoice for Demo User Functional',
      price_currency="currency_module/EUR",
      reference='1',
      ledger='automated'
    )

    cell = current_invoice.newContent(
      portal_type="Invoice Line",
      resource="service_module/slapos_reservation_fee_2",
      use="trade/sale",
      quantity_unit="unit/piece",
      base_contribution_list=[
        "base_amount/invoicing/discounted",
        "base_amount/invoicing/taxable"
      ]
    )
    cell.edit(quantity=1)
    cell.setPrice(1)

    current_invoice.plan()
    current_invoice.confirm()
    current_invoice.startBuilding()
    current_invoice.reindexObject()
    current_invoice.stop()

    self.tic()

    applied_rule = current_invoice.getCausalityRelated(portal_type="Applied Rule")
    for sm in self.portal.portal_catalog(portal_type='Simulation Movement',
                                        simulation_state=['draft', 'planned', None],
                                        left_join_list=['delivery_uid'],
                                        delivery_uid=None,
                                        path="%%%s%%" % applied_rule):

      if sm.getDelivery() is not None:
        continue
    
      root_applied_rule = sm.getRootAppliedRule()
      root_applied_rule_path = root_applied_rule.getPath()
    
      sm.getCausalityValue(portal_type='Business Link').build(
        path='%s/%%' % root_applied_rule_path)

    self.tic()
    self.login(person.getUserId())
    unpaid_invoice_list = self.portal.accounting_module.AccountingTransactionModule_getUnpaidInvoiceList()
    self.assertEqual(
      [i.getRelativeUrl() for i in unpaid_invoice_list],
      [current_invoice.getRelativeUrl()])

    self.login()

    payment = self.portal.accounting_module.newContent(
      portal_type="Payment Transaction",
      created_by_builder=1,# to prevent init script to create lines
      source_section_value=organisation,
      destination_value=person,
      start_date=DateTime('2019/10/20'),
      stop_date=DateTime('2019/10/20'),
      title='Fake Payment for Demo User Functional',
      ressource="currency_module/EUR",
      price_currency="currency_module/EUR",
      ledger='automated'
    )
    payment.newContent(
      portal_type="Accounting Transaction Line",
      destination="account_module/payable",
      source="account_module/receivable"
    )
    payment.newContent(
      portal_type="Accounting Transaction Line",
      destination="account_module/payment_to_encash",
      source="account_module/payment_to_encash"
    )
    for line in payment.contentValues():
      if line.getSource() == "account_module/payment_to_encash":
        line.setQuantity(-1)
      elif line.getSource() == "account_module/receivable":
        line.setQuantity(1)

    payment.confirm()
    payment.start()
    payment.setCausalityValue(current_invoice)
    payment.setDestinationSectionValue(person)
    
    payment.stop()
    self.tic()

    letter = None
    for line in current_invoice.contentValues():
      if line.getSource() == "account_module/receivable":
        letter = line.getGroupingReference()
    self.assertTrue(current_invoice.SaleInvoiceTransaction_isLettered())

    # is it groupped?
    is_lettered = False
    for line in payment.contentValues():
      if line.getSource() == "account_module/receivable":
        is_lettered = True
        self.assertEqual(letter, line.getGroupingReference())
    
    self.assertTrue(is_lettered)
 
    self.login(person.getUserId())
    unpaid_invoice_list = self.portal.accounting_module.AccountingTransactionModule_getUnpaidInvoiceList()
    self.assertEqual(
      [i.getRelativeUrl() for i in unpaid_invoice_list],
      [])

  #################################################################
  # SaleInvoiceTransaction_createReversalSaleInvoiceTransaction
  #################################################################
  @withAbort
  def test_createReversalSaleInvoiceTransaction_bad_portal_type(self):
    self.assertRaises(
      AssertionError,
      self.portal.SaleInvoiceTransaction_createReversalSaleInvoiceTransaction,
      batch_mode=1)

  @withAbort
  def test_createReversalSaleInvoiceTransaction_bad_payment_mode(self):
    invoice = self.createSaleInvoiceTransactionForReversal()
    invoice.edit(payment_mode="cash")
    self.tic()
    self.assertRaises(
      AssertionError,
      invoice.SaleInvoiceTransaction_createReversalSaleInvoiceTransaction,
      batch_mode=1)

  @withAbort
  def test_createReversalSaleInvoiceTransaction_bad_state(self, payment_mode='payzen'):
    invoice = self.createSaleInvoiceTransactionForReversal(payment_mode=payment_mode)
    self.portal.portal_workflow._jumpToStateFor(invoice, 'delivered')
    self.tic()
    self.assertRaises(
      AssertionError,
      invoice.SaleInvoiceTransaction_createReversalSaleInvoiceTransaction,
      batch_mode=1)

  @withAbort
  def test_createReversalSaleInvoiceTransaction_zero_price(self, payment_mode='payzen'):
    invoice = self.createSaleInvoiceTransactionForReversal(payment_mode=payment_mode)
    invoice.manage_delObjects(invoice.contentIds())
    self.tic()
    self.assertRaises(
      AssertionError,
      invoice.SaleInvoiceTransaction_createReversalSaleInvoiceTransaction,
      batch_mode=1)

  @withAbort
  def test_createReversalSaleInvoiceTransaction_wrong_trade_condition(self, payment_mode='payzen'):
    invoice = self.createSaleInvoiceTransactionForReversal(payment_mode=payment_mode)
    invoice.edit(specialise=None)
    self.tic()
    self.assertRaises(
      AssertionError,
      invoice.SaleInvoiceTransaction_createReversalSaleInvoiceTransaction,
      batch_mode=1)

  @withAbort
  def test_createReversalSaleInvoiceTransaction_wrong_ledger(self, payment_mode='payzen'):
    invoice = self.createSaleInvoiceTransactionForReversal(payment_mode=payment_mode)
    invoice.edit(ledger=None)
    self.tic()
    self.assertRaises(
      AssertionError,
      invoice.SaleInvoiceTransaction_createReversalSaleInvoiceTransaction,
      batch_mode=1)

  @withAbort
  def test_createReversalSaleInvoiceTransaction_paid(self, payment_mode='payzen'):
    invoice = self.createSaleInvoiceTransactionForReversal(payment_mode=payment_mode)
    line = invoice.contentValues(portal_type="Sale Invoice Transaction Line")[0]
    line.edit(grouping_reference="azerty")
    self.tic()
    self.assertRaises(
      AssertionError,
      invoice.SaleInvoiceTransaction_createReversalSaleInvoiceTransaction,
      batch_mode=1)

  @withAbort
  def test_createReversalSaleInvoiceTransaction_registered_payment(self, payment_mode='payzen'):
    invoice = self.createSaleInvoiceTransactionForReversal(payment_mode=payment_mode)
    payment = self.portal.accounting_module.newContent(
      portal_type="Payment Transaction",
      payment_mode=payment_mode,
      causality_value=invoice,
      destination_section=invoice.getDestinationSection(),
      created_by_builder=1 # to prevent init script to create lines
    )
    self.portal.portal_workflow._jumpToStateFor(payment, 'started')

    self.tic()
    payment.PaymentTransaction_generatePayzenId()
    self.assertRaises(
      ValueError,
      invoice.SaleInvoiceTransaction_createReversalSaleInvoiceTransaction,
      batch_mode=1)

  @withAbort
  def test_createReversalSaleInvoiceTransaction_ok(self, payment_mode='payzen'):
    invoice = self.createSaleInvoiceTransactionForReversal(payment_mode=payment_mode)
    self.tic()
    reversale_invoice = invoice.\
      SaleInvoiceTransaction_createReversalSaleInvoiceTransaction(batch_mode=1)

    self.assertEqual(invoice.getPaymentMode(""), "")
    self.assertEqual(reversale_invoice.getTitle(),
                     "Reversal Transaction for %s" % invoice.getTitle())
    self.assertEqual(reversale_invoice.getDescription(),
                     "Reversal Transaction for %s" % invoice.getTitle())
    self.assertEqual(reversale_invoice.getCausality(),
                     invoice.getRelativeUrl())
    self.assertEqual(reversale_invoice.getSimulationState(), "stopped")
    self.assertEqual(invoice.getSimulationState(), "stopped")

    invoice_line_id = invoice.contentValues(portal_type="Invoice Line")[0].getId()
    transaction_line_id = invoice.contentValues(
      portal_type="Sale Invoice Transaction Line")[0].getId()

    self.assertEqual(invoice[invoice_line_id].getQuantity(),
                     -reversale_invoice[invoice_line_id].getQuantity())
    self.assertEqual(reversale_invoice[invoice_line_id].getQuantity(), 2)

    self.assertEqual(invoice[transaction_line_id].getQuantity(),
                     -reversale_invoice[transaction_line_id].getQuantity())
    self.assertEqual(reversale_invoice[transaction_line_id].getQuantity(), 3)
    self.assertEqual(len(invoice.getMovementList()), 2)

    # Both invoice should have a grouping reference
    self.assertNotEqual(invoice[transaction_line_id].getGroupingReference(""),
                        "")
    self.assertEqual(
      invoice[transaction_line_id].getGroupingReference("1"),
      reversale_invoice[transaction_line_id].getGroupingReference("2"))

    # All references should be regenerated
    self.assertNotEqual(invoice.getReference(""),
                        reversale_invoice.getReference(""))
    self.assertNotEqual(invoice.getSourceReference(""),
                        reversale_invoice.getSourceReference(""))
    self.assertNotEqual(invoice.getDestinationReference(""),
                        reversale_invoice.getDestinationReference(""))

    self.assertTrue(invoice.SaleInvoiceTransaction_isLettered())
    self.assertTrue(reversale_invoice.SaleInvoiceTransaction_isLettered())
    
    # Another trade condition
    self.assertEqual(
      reversale_invoice.getSpecialise(),
      "sale_trade_condition_module/slapos_manual_accounting_trade_condition")
    self.tic()

  @withAbort
  def test_createReversalSaleInvoiceTransaction_ok_dont_autocancel(self, payment_mode='payzen'):
    invoice = self.createSaleInvoiceTransactionForReversal(payment_mode=payment_mode)
    payment = self.portal.accounting_module.newContent(
      portal_type="Payment Transaction",
      payment_mode=payment_mode,
      causality_value=invoice,
      destination_section=invoice.getDestinationSection(),
      created_by_builder=1 # to prevent init script to create lines
    )
    self.portal.portal_workflow._jumpToStateFor(payment, 'started')

    self.tic()
    reversale_invoice = invoice.\
      SaleInvoiceTransaction_createReversalSaleInvoiceTransaction(batch_mode=1)

    self.assertEqual(invoice.getPaymentMode(""), "")
    # Related payment is cancelled by a proper alarm.
    self.assertEqual(payment.getSimulationState(), "started")
    self.assertEqual(reversale_invoice.getTitle(),
                     "Reversal Transaction for %s" % invoice.getTitle())
    self.assertEqual(reversale_invoice.getDescription(),
                     "Reversal Transaction for %s" % invoice.getTitle())
    self.assertEqual(reversale_invoice.getCausality(),
                     invoice.getRelativeUrl())
    self.assertEqual(reversale_invoice.getSimulationState(), "stopped")
    self.assertEqual(invoice.getSimulationState(), "stopped")

    invoice_line_id = invoice.contentValues(portal_type="Invoice Line")[0].getId()
    transaction_line_id = invoice.contentValues(
      portal_type="Sale Invoice Transaction Line")[0].getId()

    self.assertEqual(invoice[invoice_line_id].getQuantity(),
                     -reversale_invoice[invoice_line_id].getQuantity())
    self.assertEqual(reversale_invoice[invoice_line_id].getQuantity(), 2)

    self.assertEqual(invoice[transaction_line_id].getQuantity(),
                     -reversale_invoice[transaction_line_id].getQuantity())
    self.assertEqual(reversale_invoice[transaction_line_id].getQuantity(), 3)
    self.assertEqual(len(invoice.getMovementList()), 2)

    # Both invoice should have a grouping reference
    self.assertNotEqual(invoice[transaction_line_id].getGroupingReference(""),
                        "")
    self.assertEqual(
      invoice[transaction_line_id].getGroupingReference("1"),
      reversale_invoice[transaction_line_id].getGroupingReference("2"))

    # All references should be regenerated
    self.assertNotEqual(invoice.getReference(""),
                        reversale_invoice.getReference(""))
    self.assertNotEqual(invoice.getSourceReference(""),
                        reversale_invoice.getSourceReference(""))
    self.assertNotEqual(invoice.getDestinationReference(""),
                        reversale_invoice.getDestinationReference(""))

    self.assertTrue(invoice.SaleInvoiceTransaction_isLettered())
    self.assertTrue(reversale_invoice.SaleInvoiceTransaction_isLettered())
    
    # Another trade condition
    self.assertEqual(
      reversale_invoice.getSpecialise(),
      "sale_trade_condition_module/slapos_manual_accounting_trade_condition")
    self.tic()

  @withAbort
  def test_createReversalSaleInvoiceTransaction_wechat_bad_state(self):
    self.test_createReversalSaleInvoiceTransaction_bad_state(payment_mode='wechat')

  @withAbort
  def test_createReversalSaleInvoiceTransaction_wechat_zero_price(self):
    self.test_createReversalSaleInvoiceTransaction_zero_price(payment_mode='wechat')

  @withAbort
  def test_createReversalSaleInvoiceTransaction_wechat_wrong_trade_condition(self):
    self.test_createReversalSaleInvoiceTransaction_wrong_trade_condition(payment_mode='wechat')

  @withAbort
  def test_createReversalSaleInvoiceTransaction_wechat_wrong_ledger(self):
    self.test_createReversalSaleInvoiceTransaction_wrong_ledger(payment_mode='wechat')

  @withAbort
  def test_createReversalSaleInvoiceTransaction_wechat_paid(self):
    self.test_createReversalSaleInvoiceTransaction_paid(payment_mode='wechat')

  @withAbort
  def test_createReversalSaleInvoiceTransaction_wechat_registered_payment(self):
    invoice = self.createSaleInvoiceTransactionForReversal(payment_mode='wechat')
    payment = self.portal.accounting_module.newContent(
      portal_type="Payment Transaction",
      payment_mode='wechat',
      causality_value=invoice,
      destination_section=invoice.getDestinationSection(),
      created_by_builder=1 # to prevent init script to create lines
    )
    self.portal.portal_workflow._jumpToStateFor(payment, 'started')

    self.tic()
    payment.PaymentTransaction_generateWechatId()
    self.assertRaises(
      ValueError,
      invoice.SaleInvoiceTransaction_createReversalSaleInvoiceTransaction,
      batch_mode=1)

  @withAbort
  def test_createReversalSaleInvoiceTransaction_wechat_ok(self):
    self.test_createReversalSaleInvoiceTransaction_ok(payment_mode='wechat')

  @withAbort
  def test_createReversalSaleInvoiceTransaction_wechat_ok_dont_autocancel(self):
    self.test_createReversalSaleInvoiceTransaction_ok_dont_autocancel(payment_mode='wechat')

  #################################################################
  # AccountingTransaction_getPaymentState
  #################################################################
  @withAbort
  def test_AccountingTransaction_getPaymentState_draft_payment(self):
    invoice = self.createSaleInvoiceTransaction()
    self.assertEqual("Cancelled", invoice.AccountingTransaction_getPaymentState())

  @withAbort
  def test_AccountingTransaction_getPaymentState_deleted_payment(self):
    invoice = self.createSaleInvoiceTransaction()
    invoice.delete()
    self.assertEqual("Cancelled", invoice.AccountingTransaction_getPaymentState())

  @withAbort
  def test_AccountingTransaction_getPaymentState_cancelled_payment(self):
    invoice = self.createSaleInvoiceTransaction()
    invoice.cancel()
    self.assertEqual("Cancelled", invoice.AccountingTransaction_getPaymentState())

  @withAbort
  def test_AccountingTransaction_getPaymentState_planned_payment(self):
    invoice = self.createSaleInvoiceTransaction()
    invoice.plan()
    self.assertEqual("Ongoing", invoice.AccountingTransaction_getPaymentState())

  @withAbort
  def test_AccountingTransaction_getPaymentState_confirmed_payment(self):
    invoice = self.createSaleInvoiceTransaction()
    invoice.setStartDate(DateTime())
    invoice.confirm()
    self.assertEqual("Ongoing", invoice.AccountingTransaction_getPaymentState())

  @withAbort
  def test_AccountingTransaction_getPaymentState_started_payment(self):
    invoice = self.createSaleInvoiceTransaction()
    invoice.start()
    self.assertEqual("Ongoing", invoice.AccountingTransaction_getPaymentState())

  @withAbort
  def test_AccountingTransaction_getPaymentState_payzen_reversed_payment(self):
    invoice =  self.createStoppedSaleInvoiceTransaction()
    self.tic()
    reversal = invoice.SaleInvoiceTransaction_createReversalSaleInvoiceTransaction(
      batch_mode=1
    )
    self.tic()
    self.assertEqual("Cancelled", invoice.AccountingTransaction_getPaymentState())
    self.assertEqual(0, invoice.getTotalPrice() + reversal.getTotalPrice())

  @withAbort
  def test_AccountingTransaction_getPaymentState_wechat_reversed_payment(self):
    invoice =  self.createStoppedSaleInvoiceTransaction(payment_mode='wechat')
    self.tic()
    reversal = invoice.SaleInvoiceTransaction_createReversalSaleInvoiceTransaction(
      batch_mode=1
    )
    self.tic()
    self.assertEqual("Cancelled", invoice.AccountingTransaction_getPaymentState())
    self.assertEqual(0, invoice.getTotalPrice() + reversal.getTotalPrice())

  def test_AccountingTransaction_getPaymentState_payzen_free_payment(self):
    invoice =  self.createStoppedSaleInvoiceTransaction(price=0)
    self.tic()
    self.assertEqual("Free!", invoice.AccountingTransaction_getPaymentState())

  def test_AccountingTransaction_getPaymentState_wechat_free_payment(self):
    invoice =  self.createStoppedSaleInvoiceTransaction(price=0, payment_mode='wechat')
    self.tic()
    self.assertEqual("Free!", invoice.AccountingTransaction_getPaymentState())

  def test_AccountingTransaction_getPaymentState_payzen_unpaid_payment(self):
    invoice =  self.createStoppedSaleInvoiceTransaction()
    # If payment is not indexed or not started the state should be Pay Now
    self.assertEqual("Pay Now", invoice.AccountingTransaction_getPaymentState())

  def test_AccountingTransaction_getPaymentState_wechat_unpaid_payment(self):
    invoice =  self.createStoppedSaleInvoiceTransaction(payment_mode='wechat')
    # If payment is not indexed or not started the state should be Pay Now
    self.assertEqual("Pay Now", invoice.AccountingTransaction_getPaymentState())

  def test_AccountingTransaction_getPaymentState_payzen_paynow_payment(self):
    project = self.addProject()
    person = self.makePerson(project)
    invoice =  self.createStoppedSaleInvoiceTransaction(
      destination_section_value=person)
    self.tic()
    self.login(person.getUserId())
    self.assertEqual("Pay Now", invoice.AccountingTransaction_getPaymentState())

  def test_AccountingTransaction_getPaymentState_wechat_paynow_payment(self):
    project = self.addProject()
    person = self.makePerson(project)
    invoice =  self.createStoppedSaleInvoiceTransaction(
      destination_section_value=person,
      payment_mode="wechat")
    self.tic()
    self.login(person.getUserId())
    self.assertEqual("Pay Now", invoice.AccountingTransaction_getPaymentState())

  def test_AccountingTransaction_getPaymentState_payzen_waiting_payment(self):
    project = self.addProject()
    person = self.makePerson(project)
    invoice =  self.createStoppedSaleInvoiceTransaction(
      destination_section_value=person)

    payment = self.portal.accounting_module.newContent(
      portal_type="Payment Transaction",
      payment_mode='payzen',
      ledger='automated',
      causality_value=invoice,
      destination_section=invoice.getDestinationSection(),
      created_by_builder=1 # to prevent init script to create lines
    )
    self.portal.portal_workflow._jumpToStateFor(payment, 'started')
    payment.PaymentTransaction_generatePayzenId()
    self.tic()
    self.login(person.getUserId())
    self.assertEqual("Waiting for payment confirmation",
                      invoice.AccountingTransaction_getPaymentState())

  def test_AccountingTransaction_getPaymentState_wechat_waiting_payment(self):
    project = self.addProject()
    person = self.makePerson(project)
    invoice =  self.createStoppedSaleInvoiceTransaction(
      destination_section_value=person,
      payment_mode='wechat')

    payment = self.portal.accounting_module.newContent(
      portal_type="Payment Transaction",
      payment_mode='wechat',
      ledger='automated',
      causality_value=invoice,
      destination_section=invoice.getDestinationSection(),
      created_by_builder=1 # to prevent init script to create lines
    )
    self.portal.portal_workflow._jumpToStateFor(payment, 'started')
    payment.PaymentTransaction_generateWechatId()
    self.tic()
    self.login(person.getUserId())
    self.assertEqual("Waiting for payment confirmation",
                      invoice.AccountingTransaction_getPaymentState())

  def test_AccountingTransaction_getPaymentState_payzen_papaid_payment(self):
    invoice = self.createStoppedSaleInvoiceTransaction()
    self.tic()
    for line in invoice.getMovementList(self.portal.getPortalAccountingMovementTypeList()):
      node_value = line.getSourceValue(portal_type='Account')
      if node_value.getAccountType() == 'asset/receivable':
        line.setGroupingReference("TEST%s" % self.new_id)
    self.assertEqual("Paid",
                      invoice.AccountingTransaction_getPaymentState())

  def test_AccountingTransaction_getPaymentState_wechat_paid_payment(self):
    invoice =  self.createStoppedSaleInvoiceTransaction(payment_mode='wechat')
    self.tic()
    for line in invoice.getMovementList(self.portal.getPortalAccountingMovementTypeList()):
      node_value = line.getSourceValue(portal_type='Account')
      if node_value.getAccountType() == 'asset/receivable':
        line.setGroupingReference("TEST%s" % self.new_id)
    self.assertEqual("Paid",
                      invoice.AccountingTransaction_getPaymentState())

  def test_AccountingTransaction_getPaymentState_wire_transfer_paid_payment(self):
    invoice =  self.createStoppedSaleInvoiceTransaction(payment_mode='wire_transfer')
    self.tic()
    for line in invoice.getMovementList(self.portal.getPortalAccountingMovementTypeList()):
      node_value = line.getSourceValue(portal_type='Account')
      if node_value.getAccountType() == 'asset/receivable':
        line.setGroupingReference("TEST%s" % self.new_id)
    self.assertEqual("Paid",
                      invoice.AccountingTransaction_getPaymentState())

  #################################################################
  # Base_getReceivableAccountList
  #################################################################
  def test_Base_getReceivableAccountList(self):
    account_list = self.portal.Base_getReceivableAccountList()

    self.assertIn('account_module/receivable',
      [i.getRelativeUrl() for i in account_list])

  #################################################################
  # PaymentTransaction_start
  #################################################################
  def test_PaymentTransaction_start(self):

    sale_invoice_transaction = self.portal.accounting_module.newContent(
      portal_type="Sale Invoice Transaction",
      start_date=DateTime()
    )
    payment_transaction = self.portal.accounting_module.newContent(
      portal_type="Payment Transaction",
      start_date=DateTime()
    )

    self.assertRaises(Unauthorized,
      payment_transaction.PaymentTransaction_start,
      REQUEST=self.portal.REQUEST)

    self.assertRaises(Unauthorized,
      sale_invoice_transaction.PaymentTransaction_start,
      REQUEST=self.portal.REQUEST)

    self.assertRaises(Unauthorized,
      sale_invoice_transaction.PaymentTransaction_start,
      REQUEST=None)

    payment_transaction.PaymentTransaction_start()
    self.assertEqual("started",
      payment_transaction.getSimulationState())

