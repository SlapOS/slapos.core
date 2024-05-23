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

from DateTime import DateTime
from zExceptions import Unauthorized


class TestSlapOSAccounting(SlapOSTestCaseMixin):

  def createIntegrationSite(self):
    # Include a simple Integration site, which is required for
    # PaymentTransaction_generatePayzenId
    integration_site = self.portal.portal_integrations.newContent(
      title="Integration site for test_AccountingTransaction_getPaymentState_payzen_waiting_payment",
      reference="payzen",
      portal_type="Integration Site"
    )
    integration_site.newContent(
      id="Causality",
      portal_type="Integration Base Category Mapping",
      default_source_reference="Causality",
      default_destination_reference="causality"
    )
    resource_map = integration_site.newContent(
      id="Resource",
      portal_type="Integration Base Category Mapping",
      default_source_reference="Resource",
      default_destination_reference="resource"
    )
    resource_map.newContent(
      id='978',
      portal_type="Integration Category Mapping",
      default_destination_reference='resource/currency_module/EUR',
      default_source_reference='978'
    )
    return integration_site

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
      created_by_builder=1  # to prevent init script to create lines
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
  def test_createReversalSaleInvoiceTransaction_zero_price(self, payment_mode='payzen'):
    invoice = self.createSaleInvoiceTransactionForReversal(payment_mode=payment_mode)
    invoice.manage_delObjects(invoice.contentIds())
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
      destination=invoice.getDestination(),
      destination_section=invoice.getDestinationSection(),
      created_by_builder=1  # to prevent init script to create lines
    )
    self.portal.portal_workflow._jumpToStateFor(payment, 'started')

    system_preference = self.portal.portal_preferences.slapos_default_system_preference
    older_integration_site = system_preference.getPreferredPayzenIntegrationSite()
    
    integration_site = self.createIntegrationSite()
    system_preference.setPreferredPayzenIntegrationSite(
      integration_site.getRelativeUrl()
    )

    try:
      self.tic()
      payment.PaymentTransaction_generatePayzenId()
      self.assertRaises(
        ValueError,
        invoice.SaleInvoiceTransaction_createReversalSaleInvoiceTransaction,
        batch_mode=1)
    finally:
      self.portal.portal_integrations.manage_delObjects(
        ids=[integration_site.getId()])
      system_preference.setPreferredPayzenIntegrationSite(
        older_integration_site
      )
    

  @withAbort
  def test_createReversalSaleInvoiceTransaction_ok(self, payment_mode='payzen'):
    invoice = self.createSaleInvoiceTransactionForReversal(payment_mode=payment_mode)
    self.tic()
    reversale_invoice = invoice.\
      SaleInvoiceTransaction_createReversalSaleInvoiceTransaction(batch_mode=1)

    self.assertEqual(invoice.getPaymentMode(""), payment_mode)
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
      destination=invoice.getDestination(),
      destination_section=invoice.getDestinationSection(),
      created_by_builder=1  # to prevent init script to create lines
    )
    self.portal.portal_workflow._jumpToStateFor(payment, 'started')

    self.tic()
    self.assertRaises(
      ValueError,
      invoice.SaleInvoiceTransaction_createReversalSaleInvoiceTransaction,
      batch_mode=1)

  @withAbort
  def test_createReversalSaleInvoiceTransaction_wechat_zero_price(self):
    self.test_createReversalSaleInvoiceTransaction_zero_price(payment_mode='wechat')

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
      destination=invoice.getDestination(),
      destination_section=invoice.getDestinationSection(),
      created_by_builder=1  # to prevent init script to create lines
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
    invoice = self.createStoppedSaleInvoiceTransaction()
    self.tic()
    reversal = invoice.SaleInvoiceTransaction_createReversalSaleInvoiceTransaction(
      batch_mode=1
    )
    self.tic()
    self.assertEqual("Paid", invoice.AccountingTransaction_getPaymentState())
    self.assertEqual(0, invoice.getTotalPrice() + reversal.getTotalPrice())
    self.assertTrue(invoice.SaleInvoiceTransaction_isLettered())
    self.assertTrue(reversal.SaleInvoiceTransaction_isLettered())

  @withAbort
  def test_AccountingTransaction_getPaymentState_wechat_reversed_payment(self):
    invoice = self.createStoppedSaleInvoiceTransaction(payment_mode='wechat')
    self.tic()
    reversal = invoice.SaleInvoiceTransaction_createReversalSaleInvoiceTransaction(
      batch_mode=1
    )
    self.tic()
    self.assertEqual("Paid", invoice.AccountingTransaction_getPaymentState())
    self.assertEqual(0, invoice.getTotalPrice() + reversal.getTotalPrice())

  def test_AccountingTransaction_getPaymentState_payzen_free_payment(self):
    invoice = self.createStoppedSaleInvoiceTransaction(price=0)
    self.tic()
    self.assertEqual("Free!", invoice.AccountingTransaction_getPaymentState())

  def test_AccountingTransaction_getPaymentState_wechat_free_payment(self):
    invoice = self.createStoppedSaleInvoiceTransaction(price=0, payment_mode='wechat')
    self.tic()
    self.assertEqual("Free!", invoice.AccountingTransaction_getPaymentState())

  def test_AccountingTransaction_getPaymentState_payzen_unpaid_payment(self):
    invoice = self.createStoppedSaleInvoiceTransaction()
    # If payment is not indexed or not started the state should be Pay Now
    self.assertEqual("Pay Now", invoice.AccountingTransaction_getPaymentState())

  def test_AccountingTransaction_getPaymentState_wechat_unpaid_payment(self):
    invoice = self.createStoppedSaleInvoiceTransaction(payment_mode='wechat')
    # If payment is not indexed or not started the state should be Pay Now
    self.assertEqual("Pay Now", invoice.AccountingTransaction_getPaymentState())

  def test_AccountingTransaction_getPaymentState_payzen_paynow_payment(self):
    project = self.addProject()
    person = self.makePerson(project)
    invoice = self.createStoppedSaleInvoiceTransaction(
      destination_section_value=person)
    self.tic()
    self.login(person.getUserId())
    self.assertEqual("Pay Now", invoice.AccountingTransaction_getPaymentState())

  def test_AccountingTransaction_getPaymentState_wechat_paynow_payment(self):
    project = self.addProject()
    person = self.makePerson(project)
    invoice = self.createStoppedSaleInvoiceTransaction(
      destination_section_value=person,
      payment_mode="wechat")
    self.tic()
    self.login(person.getUserId())
    self.assertEqual("Pay Now", invoice.AccountingTransaction_getPaymentState())

  def test_AccountingTransaction_getPaymentState_payzen_waiting_payment(self):
    project = self.addProject()
    person = self.makePerson(project)
    invoice = self.createStoppedSaleInvoiceTransaction(
      destination_section_value=person)

    payment = self.portal.accounting_module.newContent(
      portal_type="Payment Transaction",
      payment_mode='payzen',
      ledger='automated',
      causality_value=invoice,
      destination=invoice.getDestination(),
      destination_section=invoice.getDestinationSection(),
      created_by_builder=1  # to prevent init script to create lines
    )
    self.portal.portal_workflow._jumpToStateFor(payment, 'started')

    system_preference = self.portal.portal_preferences.slapos_default_system_preference
    older_integration_site = system_preference.getPreferredPayzenIntegrationSite()
    
    integration_site = self.createIntegrationSite()
    system_preference.setPreferredPayzenIntegrationSite(
      integration_site.getRelativeUrl()
    )

    try:
      payment.PaymentTransaction_generatePayzenId()
      self.tic()
      self.login(person.getUserId())
      self.assertEqual("Waiting for payment confirmation",
                      invoice.AccountingTransaction_getPaymentState())
    finally:
      self.portal.portal_integrations.manage_delObjects(
        ids=[integration_site.getId()])
      system_preference.setPreferredPayzenIntegrationSite(
        older_integration_site
      )

  def test_AccountingTransaction_getPaymentState_wechat_waiting_payment(self):
    project = self.addProject()
    person = self.makePerson(project)
    invoice = self.createStoppedSaleInvoiceTransaction(
      destination_section_value=person,
      payment_mode='wechat')

    payment = self.portal.accounting_module.newContent(
      portal_type="Payment Transaction",
      payment_mode='wechat',
      ledger='automated',
      causality_value=invoice,
      destination=invoice.getDestination(),
      destination_section=invoice.getDestinationSection(),
      created_by_builder=1  # to prevent init script to create lines
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
    invoice = self.createStoppedSaleInvoiceTransaction(payment_mode='wechat')
    self.tic()
    for line in invoice.getMovementList(self.portal.getPortalAccountingMovementTypeList()):
      node_value = line.getSourceValue(portal_type='Account')
      if node_value.getAccountType() == 'asset/receivable':
        line.setGroupingReference("TEST%s" % self.new_id)
    self.assertEqual("Paid",
                      invoice.AccountingTransaction_getPaymentState())

  def test_AccountingTransaction_getPaymentState_wire_transfer_paid_payment(self):
    invoice = self.createStoppedSaleInvoiceTransaction(payment_mode='wire_transfer')
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
  # Delivery_fixBaseContributionTaxableRate
  #################################################################
  def _createEntityForVatCalculation(self, portal_type, region=None, vat_code=None):
    module = self.portal.getDefaultModuleValue(portal_type)
    return module.newContent(
      portal_type=portal_type,
      default_address_region=region,
      vat_code=vat_code
    )

  def _createSalePackingListForVatCalculation(self, source_section_value,
                                              destination_section_value):
    delivery = self.portal.sale_packing_list_module.newContent(
      portal_type='Sale Packing List',
      source_section_value=source_section_value,
      destination_section_value=destination_section_value
    )
    line = delivery.newContent(
      portal_type='Sale Packing List Line',
      resource='service_module/slapos_virtual_master_subscription'
    )
    self.assertTrue('base_amount/invoicing/taxable' in line.getBaseContributionList())
    return delivery, line

  @withAbort
  def test_fixBaseContributionTaxableRate_unauthorized(self):
    self.assertRaises(
      Unauthorized,
      self.portal.Delivery_fixBaseContributionTaxableRate,
      REQUEST=1)

  @withAbort
  def test_fixBaseContributionTaxableRate_noSourceOrganisation(self):
    delivery, line = self._createSalePackingListForVatCalculation(
      self._createEntityForVatCalculation(portal_type='Person',
                                          region='europe/west/france'),
      self._createEntityForVatCalculation(portal_type='Person',
                                          region='europe/west/france'),
    )
    delivery.Delivery_fixBaseContributionTaxableRate()
    # No change
    self.assertTrue('base_amount/invoicing/taxable' in line.getBaseContributionList())

  @withAbort
  def test_fixBaseContributionTaxableRate_noSourceRegion(self):
    delivery, line = self._createSalePackingListForVatCalculation(
      self._createEntityForVatCalculation(portal_type='Organisation'),
      self._createEntityForVatCalculation(portal_type='Person',
                                          region='europe/west/france'),
    )
    delivery.Delivery_fixBaseContributionTaxableRate()
    # No change
    self.assertTrue('base_amount/invoicing/taxable' in line.getBaseContributionList())

  @withAbort
  def test_fixBaseContributionTaxableRate_notManagedSourceRegion(self):
    delivery, line = self._createSalePackingListForVatCalculation(
      self._createEntityForVatCalculation(portal_type='Organisation',
                                          region='europe/west/germany'),
      self._createEntityForVatCalculation(portal_type='Person',
                                          region='europe/west/france'),
    )
    delivery.Delivery_fixBaseContributionTaxableRate()
    # No change
    self.assertTrue('base_amount/invoicing/taxable' in line.getBaseContributionList())

  @withAbort
  def test_fixBaseContributionTaxableRate_franceNotDestinationRegion(self):
    delivery, line = self._createSalePackingListForVatCalculation(
      self._createEntityForVatCalculation(portal_type='Organisation',
                                          region='europe/west/france'),
      self._createEntityForVatCalculation(portal_type='Person'),
    )
    delivery.Delivery_fixBaseContributionTaxableRate()
    # No change
    self.assertTrue('base_amount/invoicing/taxable' in line.getBaseContributionList())

  @withAbort
  def test_fixBaseContributionTaxableRate_franceToFrancePerson(self):
    delivery, line = self._createSalePackingListForVatCalculation(
      self._createEntityForVatCalculation(portal_type='Organisation',
                                          region='europe/west/france'),
      self._createEntityForVatCalculation(portal_type='Person',
                                          region='europe/west/france'),
    )
    delivery.Delivery_fixBaseContributionTaxableRate()
    # No change
    self.assertTrue('base_amount/invoicing/taxable/vat/normal_rate' in line.getBaseContributionList())

  @withAbort
  def test_fixBaseContributionTaxableRate_franceToFranceOrganisation(self):
    delivery, line = self._createSalePackingListForVatCalculation(
      self._createEntityForVatCalculation(portal_type='Organisation',
                                          region='europe/west/france'),
      self._createEntityForVatCalculation(portal_type='Organisation',
                                          region='europe/west/france',
                                          vat_code='foobar'),
    )
    delivery.Delivery_fixBaseContributionTaxableRate()
    # No change
    self.assertTrue('base_amount/invoicing/taxable/vat/normal_rate' in line.getBaseContributionList())

  @withAbort
  def test_fixBaseContributionTaxableRate_franceToFranceOrganisationWithoutVatCode(self):
    delivery, line = self._createSalePackingListForVatCalculation(
      self._createEntityForVatCalculation(portal_type='Organisation',
                                          region='europe/west/france'),
      self._createEntityForVatCalculation(portal_type='Organisation',
                                          region='europe/west/france'),
    )
    delivery.Delivery_fixBaseContributionTaxableRate()
    # No change
    self.assertTrue('base_amount/invoicing/taxable' in line.getBaseContributionList())

  @withAbort
  def test_fixBaseContributionTaxableRate_franceToEuropePerson(self):
    delivery, line = self._createSalePackingListForVatCalculation(
      self._createEntityForVatCalculation(portal_type='Organisation',
                                          region='europe/west/france'),
      self._createEntityForVatCalculation(portal_type='Person',
                                          region='europe/west/germany'),
    )
    delivery.Delivery_fixBaseContributionTaxableRate()
    # No change
    self.assertTrue('base_amount/invoicing/taxable/vat/normal_rate' in line.getBaseContributionList())

  @withAbort
  def test_fixBaseContributionTaxableRate_franceToEuropeOrganisation(self):
    delivery, line = self._createSalePackingListForVatCalculation(
      self._createEntityForVatCalculation(portal_type='Organisation',
                                          region='europe/west/france'),
      self._createEntityForVatCalculation(portal_type='Organisation',
                                          region='europe/west/germany',
                                          vat_code='foobar'),
    )
    delivery.Delivery_fixBaseContributionTaxableRate()
    # No change
    self.assertTrue('base_amount/invoicing/taxable/vat/zero_rate' in line.getBaseContributionList())

  @withAbort
  def test_fixBaseContributionTaxableRate_franceToEuropeOrganisationWithoutVatCode(self):
    delivery, line = self._createSalePackingListForVatCalculation(
      self._createEntityForVatCalculation(portal_type='Organisation',
                                          region='europe/west/france'),
      self._createEntityForVatCalculation(portal_type='Organisation',
                                          region='europe/west/germany'),
    )
    delivery.Delivery_fixBaseContributionTaxableRate()
    # No change
    self.assertTrue('base_amount/invoicing/taxable' in line.getBaseContributionList())

  @withAbort
  def test_fixBaseContributionTaxableRate_franceToWorldPerson(self):
    delivery, line = self._createSalePackingListForVatCalculation(
      self._createEntityForVatCalculation(portal_type='Organisation',
                                          region='europe/west/france'),
      self._createEntityForVatCalculation(portal_type='Person',
                                          region='america/south/brazil'),
    )
    delivery.Delivery_fixBaseContributionTaxableRate()
    # No change
    self.assertTrue('base_amount/invoicing/taxable/vat/zero_rate' in line.getBaseContributionList())

  @withAbort
  def test_fixBaseContributionTaxableRate_franceToWorldOrganisation(self):
    delivery, line = self._createSalePackingListForVatCalculation(
      self._createEntityForVatCalculation(portal_type='Organisation',
                                          region='europe/west/france'),
      self._createEntityForVatCalculation(portal_type='Organisation',
                                          region='america/south/brazil'),
    )
    delivery.Delivery_fixBaseContributionTaxableRate()
    # No change
    self.assertTrue('base_amount/invoicing/taxable/vat/zero_rate' in line.getBaseContributionList())
