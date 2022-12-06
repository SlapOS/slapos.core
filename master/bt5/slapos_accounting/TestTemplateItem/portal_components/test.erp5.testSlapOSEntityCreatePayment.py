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

class TestSlapOSEntityCreatePaymentMixin(SlapOSTestCaseMixin):
  
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
    self.assertEqual('confirmed', payment.getSimulationState())
    self.assertSameSet([], payment.checkConsistency())
    self.assertSameSet([invoice], payment.getCausalityValueList())
    self.assertSameSet([], payment.getCausalityRelatedValueList(
        portal_type='Applied Rule'))
    expected_set = [
      'causality/%s' % invoice.getRelativeUrl(),
      'destination_section/%s' % invoice.getDestinationSection(),
      'price_currency/%s' % invoice.getPriceCurrency(),
      'resource/%s' % invoice.getResource(),
      'source_payment/organisation_module/slapos/bank_account',
      'payment_mode/%s' % self.payment_mode,
      'source_section/%s' % invoice.getSourceSection(),
    ]
    self.assertSameSet(expected_set, payment.getCategoryList())
    self.assertEqual(invoice.getStartDate(), payment.getStartDate())
    self.assertEqual(invoice.getStopDate(), payment.getStopDate())

    movement_list = payment.getMovementList()
    self.assertEqual(2, len(movement_list))
    bank_list = [q for q in movement_list
        if q.getSource() == 'account_module/payment_to_encash']
    rec_list = [q for q in movement_list
        if q.getSource() == 'account_module/receivable']
    self.assertEqual(1, len(bank_list))
    self.assertEqual(1, len(rec_list))

    def assertLine(line, quantity, category_list):
      self.assertTrue(line.hasStartDate())
      self.assertTrue(line.hasStopDate())
      self.assertEqual(quantity, line.getQuantity())
      self.assertSameSet(category_list, line.getCategoryList())

    invoice_amount = self.sumReceivable(invoice)
    assertLine(bank_list[0], invoice_amount, [
        'destination/account_module/payment_to_encash',
        'source/account_module/payment_to_encash'])
    assertLine(rec_list[0], -1 * invoice_amount, [
        'destination/account_module/payable',
        'source/account_module/receivable'])

  def fullBuild(self, person, invoice_list):
    payment = person.Entity_createPaymentTransaction(invoice_list)
    self.assertNotEqual(None, payment)
    return payment

  def resetPaymentTag(self, invoice):
    payment_tag = "sale_invoice_transaction_create_payment_%s" % invoice.getUid()
    invoice.REQUEST.set(payment_tag, None)

  def _test(self):
    person = self.portal.person_module.template_member\
        .Base_createCloneDocument(batch_mode=1)
    invoice = self.portal.accounting_module.template_sale_invoice_transaction\
        .Base_createCloneDocument(batch_mode=1)
    invoice.edit(destination_section=person.getRelativeUrl(),
                 payment_mode=self.payment_mode)
    invoice.confirm()
    invoice.stop()
    self.tic()
    payment = self.fullBuild(person, [invoice])
    self.tic()
    self.assertPayment(payment, invoice)

  def _test_twice(self):
    person = self.portal.person_module.template_member\
        .Base_createCloneDocument(batch_mode=1)
    invoice = self.portal.accounting_module.template_sale_invoice_transaction\
        .Base_createCloneDocument(batch_mode=1)
    invoice.edit(destination_section=person.getRelativeUrl(),
                 payment_mode=self.payment_mode)
    invoice.confirm()
    invoice.stop()
    self.tic()
    payment = self.fullBuild(person, [invoice])
    self.assertPayment(payment, invoice)
    self.tic()
    self.resetPaymentTag(invoice)

    # Create twice, generate 2 payments
    payment = self.fullBuild(person, [invoice])
    self.assertPayment(payment, invoice)

  def _test_twice_transaction(self):
    person = self.portal.person_module.template_member\
        .Base_createCloneDocument(batch_mode=1)
    invoice = self.portal.accounting_module.template_sale_invoice_transaction\
        .Base_createCloneDocument(batch_mode=1)
    invoice.edit(destination_section=person.getRelativeUrl(),
                 payment_mode=self.payment_mode)
    invoice.confirm()
    invoice.stop()
    self.tic()
    payment = self.fullBuild(person, [invoice])
    self.assertRaises(ValueError, person.Entity_createPaymentTransaction, [invoice])
    self.tic()
    self.assertPayment(payment, invoice)

  def _test_twice_indexation(self):
    person = self.portal.person_module.template_member\
        .Base_createCloneDocument(batch_mode=1)
    invoice = self.portal.accounting_module.template_sale_invoice_transaction\
        .Base_createCloneDocument(batch_mode=1)
    invoice.edit(destination_section=person.getRelativeUrl(),
                 payment_mode=self.payment_mode)
    invoice.confirm()
    invoice.stop()
    self.tic()
    payment = self.fullBuild(person, [invoice])
    self.commit()
    # Request was over, so emulate start a new one
    self.resetPaymentTag(invoice)

    # Should we take into account that a payment is ongoing?
    payment2 = self.fullBuild(person, [invoice])

    self.tic()
    self.assertPayment(payment, invoice)
    self.assertPayment(payment2, invoice)
    

  def _test_cancelled_payment(self):
    person = self.portal.person_module.template_member\
        .Base_createCloneDocument(batch_mode=1)
    invoice = self.portal.accounting_module.template_sale_invoice_transaction\
        .Base_createCloneDocument(batch_mode=1)
    invoice.edit(destination_section=person.getRelativeUrl(),
                 payment_mode=self.payment_mode)
    invoice.confirm()
    invoice.stop()
    self.tic()
    payment = self.fullBuild(person, [invoice])
    payment.cancel()
    self.tic()
    self.resetPaymentTag(invoice)

    payment = self.fullBuild(person, [invoice])
    self.tic()
    self.assertPayment(payment, invoice)

  def _test_two_invoices(self):
    person = self.portal.person_module.template_member\
        .Base_createCloneDocument(batch_mode=1)
    invoice_1 = self.portal.accounting_module.template_sale_invoice_transaction\
        .Base_createCloneDocument(batch_mode=1)
    invoice_1.edit(destination_section=person.getRelativeUrl(),
                 payment_mode=self.payment_mode)
    invoice_1.confirm()
    invoice_1.stop()
    invoice_2 = self.portal.accounting_module.template_sale_invoice_transaction\
        .Base_createCloneDocument(batch_mode=1)
    invoice_2.edit(destination_section=person.getRelativeUrl(),
                 payment_mode=self.payment_mode)
    invoice_2.confirm()
    invoice_2.stop()
    self.tic()
    payment_list = [self.fullBuild(person, [invoice_1]),
                    self.fullBuild(person, [invoice_2])]
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
    person = self.portal.person_module.template_member\
        .Base_createCloneDocument(batch_mode=1)
    invoice = self.portal.accounting_module.template_sale_invoice_transaction\
        .Base_createCloneDocument(batch_mode=1)
    invoice.edit(destination_section=person.getRelativeUrl(),
                 payment_mode=self.payment_mode)
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
