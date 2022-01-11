# -*- coding:utf-8 -*-
##############################################################################
#
# Copyright (c) 2022 Nexedi SA and Contributors. All Rights Reserved.
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

from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixin
from DateTime import DateTime

class TestSlapOSEntityCreatePaymentMixin(SlapOSTestCaseMixin):

  def makeSaleInvoiceTransaction(self, person=None):
    project = self.addProject()
    organisation = self.portal.organisation_module.newContent(
      portal_type="Organisation"
    )
    bank_account = organisation.newContent(
      portal_type="Bank Account"
    )
    currency = self.portal.currency_module.newContent(
      portal_type="Currency",
      base_unit_quantity=0.1
    )
    if person is None:
      person = self.portal.person_module\
          .newContent(portal_type="Person")

    invoice = self.createSaleInvoiceTransaction(
      source_value=organisation,
      source_section_value=organisation,
      source_payment_value=bank_account,
      destination_section_value=person,
      destination_project_value=project,
      resource_value=currency,
      price_currency_value=currency,
      ledger='automated',
      payment_mode=self.payment_mode,
      start_date=DateTime('2012/01/01'),
      stop_date=DateTime('2012/01/15'),
      created_by_builder=1 # to prevent init script to create lines
    )
    for line_kw in [{
      'destination': 'account_module/payable',
      'source': 'account_module/receivable',
      'quantity': -1.0
    }, {
      'destination': 'account_module/purchase',
      'source': 'account_module/sales',
      'quantity': 0.84
    }, {
      'destination': 'account_module/refundable_vat',
      'source': 'account_module/coll_vat',
      'quantity': 0.16
    }]:
      invoice.newContent(
        portal_type="Sale Invoice Transaction Line",
        resource_value=currency,
        price=1.0,
        **line_kw
      )
    return person, invoice

  def sumReceivable(self, payment_transaction):
    quantity = .0
    default_source_uid = self.portal.restrictedTraverse(
        'account_module/receivable').getUid()
    for line in payment_transaction.searchFolder(
        portal_type=self.portal.getPortalAccountingMovementTypeList(),
        default_source_uid=default_source_uid):
      quantity += line.getQuantity()
    return quantity

  def assertPayment(self, payment, invoice):
    self.assertEqual(self.sumReceivable(invoice), payment\
        .PaymentTransaction_getTotalPayablePrice())
    self.assertEqual('started', payment.getSimulationState())
    self.assertSameSet([], payment.checkConsistency())
    self.assertSameSet([invoice], payment.getCausalityValueList())
    self.assertSameSet([], payment.getCausalityRelatedValueList(
        portal_type='Applied Rule'))
    expected_set = [
      'causality/%s' % invoice.getRelativeUrl(),
      'destination_section/%s' % invoice.getDestinationSection(),
      'resource/%s' % invoice.getPriceCurrency(),
      'source_payment/%s' % invoice.getSourcePayment(),
      'payment_mode/%s' % self.payment_mode,
      'source_section/%s' % invoice.getSourceSection(),
      'ledger/%s' % invoice.getLedger(),
    ]
    self.assertSameSet(expected_set, payment.getCategoryList())
    self.assertEqual(invoice.getStartDate(), payment.getStartDate())
    self.assertEqual(invoice.getStartDate(), payment.getStopDate())

    invoice_movement_list = invoice.getMovementList()
    movement_list = payment.getMovementList()
    bank_list = [q for q in movement_list
        if q.getSource() == 'account_module/payment_to_encash']
    rec_list = [q for q in movement_list
        if q.getSource() == 'account_module/receivable']
    self.assertEqual(1, len(bank_list))
    self.assertEqual(len([q for q in invoice_movement_list
        if q.getSource() == 'account_module/receivable']), len(rec_list))

    def assertLine(line, quantity, category_list):
      self.assertFalse(line.hasStartDate())
      self.assertFalse(line.hasStopDate())
      self.assertEqual(quantity, line.getQuantity())
      self.assertSameSet(category_list, line.getCategoryList())

    invoice_amount = self.sumReceivable(invoice)
    assertLine(bank_list[0], invoice_amount, [
        'destination/account_module/payment_to_encash',
        'source/account_module/payment_to_encash'])
    for rec in rec_list:
      assertLine(rec, -invoice_amount / len(rec_list), [
          'destination/account_module/payable',
          'source/account_module/receivable'])

  def fullBuild(self, person, invoice_list):
    payment = person.Entity_createPaymentTransaction(person.Entity_getOutstandingAmountList(
      include_planned=False,
      section_uid=invoice_list[0].getSourceSectionUid(),
      resource_uid=invoice_list[0].getPriceCurrencyUid(),
      ledger_uid=invoice_list[0].getLedgerUid(),
      group_by_node=False
    ), payment_mode=self.payment_mode, start_date=invoice_list[0].getStartDate())
    self.assertNotEqual(None, payment)
    return payment

  def resetPaymentTag(self, person):
    payment_tag = "Entity_createPaymentTransaction_%s" % person.getUid()
    person.REQUEST.set(payment_tag, None)

  def _test(self):
    person, invoice = self.makeSaleInvoiceTransaction()
    invoice.confirm()
    invoice.stop()
    self.tic()
    payment = self.fullBuild(person, [invoice])
    self.tic()
    self.assertPayment(payment, invoice)

  def _test_twice(self):
    person, invoice = self.makeSaleInvoiceTransaction()
    invoice.confirm()
    invoice.stop()
    self.tic()
    payment = self.fullBuild(person, [invoice])
    self.assertPayment(payment, invoice)
    self.tic()
    self.resetPaymentTag(person)

    # Create twice, generate 2 payments
    payment = self.fullBuild(person, [invoice])
    self.assertPayment(payment, invoice)

  def _test_twice_transaction(self):
    person, invoice = self.makeSaleInvoiceTransaction()
    invoice.confirm()
    invoice.stop()
    self.tic()
    payment = self.fullBuild(person, [invoice])
    self.assertRaises(ValueError, person.Entity_createPaymentTransaction, [invoice])
    self.tic()
    self.assertPayment(payment, invoice)

  def _test_twice_indexation(self):
    person, invoice = self.makeSaleInvoiceTransaction()
    invoice.confirm()
    invoice.stop()
    self.tic()
    payment = self.fullBuild(person, [invoice])
    self.commit()
    # Request was over, so emulate start a new one
    self.resetPaymentTag(person)

    # Should we take into account that a payment is ongoing?
    payment2 = self.fullBuild(person, [invoice])

    self.tic()
    self.assertPayment(payment, invoice)
    self.assertPayment(payment2, invoice)

  def _test_cancelled_payment(self):
    person, invoice = self.makeSaleInvoiceTransaction()
    invoice.confirm()
    invoice.stop()
    self.tic()
    payment = self.fullBuild(person, [invoice])
    payment.cancel()
    self.tic()
    self.resetPaymentTag(person)

    payment = self.fullBuild(person, [invoice])
    self.tic()
    self.assertPayment(payment, invoice)

  def _test_two_invoices(self):
    person, invoice_1 = self.makeSaleInvoiceTransaction()
    invoice_1.confirm()
    invoice_1.stop()
    _, invoice_2 = self.makeSaleInvoiceTransaction(person=person)
    invoice_2.confirm()
    invoice_2.stop()
    self.tic()
    payment_list = [self.fullBuild(person, [invoice_1])]
    self.resetPaymentTag(person)
    payment_list.append(self.fullBuild(person, [invoice_2]))
    self.tic()

    self.assertEqual(2, len(payment_list))

    payment_1_list = [q for q in payment_list
        if q.getCausalityValue() == invoice_1]
    payment_2_list = [q for q in payment_list
        if q.getCausalityValue() == invoice_2]
    self.assertEqual(1, len(payment_1_list))
    self.assertEqual(1, len(payment_2_list))
    payment_1 = payment_1_list[0]
    payment_2 = payment_2_list[0]
    self.assertPayment(payment_1, invoice_1)
    self.assertPayment(payment_2, invoice_2)

  def _test_two_lines(self):
    person, invoice = self.makeSaleInvoiceTransaction()
    self.tic()
    default_source_uid = self.portal.restrictedTraverse(
        'account_module/receivable').getUid()
    modified = False
    for line in invoice.searchFolder(
        portal_type=self.portal.getPortalAccountingMovementTypeList(),
        default_source_uid=default_source_uid):
      quantity = line.getQuantity() / 2
      line.edit(quantity=quantity)
      line.getObject().Base_createCloneDocument(batch_mode=1).edit(
          quantity=quantity)
      modified = True
      break
    self.assertTrue(modified)

    invoice.confirm()
    invoice.stop()
    self.tic()
    payment = self.fullBuild(person, [invoice])
    self.tic()
    self.assertPayment(payment, invoice)

class TestSlapOSEntityCreatePayment(TestSlapOSEntityCreatePaymentMixin):
  payment_mode = "wire_transfer"

  test = TestSlapOSEntityCreatePaymentMixin._test
  test_twice = TestSlapOSEntityCreatePaymentMixin._test_twice
  test_twice_transaction = TestSlapOSEntityCreatePaymentMixin._test_twice_transaction
  test_twice_indexation = TestSlapOSEntityCreatePaymentMixin._test_twice_indexation
  test_cancelled_payment = TestSlapOSEntityCreatePaymentMixin._test_cancelled_payment
  test_two_invoices = TestSlapOSEntityCreatePaymentMixin._test_two_invoices
  test_two_lines = TestSlapOSEntityCreatePaymentMixin._test_two_lines
