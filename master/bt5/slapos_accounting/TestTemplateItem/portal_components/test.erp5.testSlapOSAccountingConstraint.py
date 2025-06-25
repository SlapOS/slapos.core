# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2012 Nexedi SA and Contributors. All Rights Reserved.
#
##############################################################################
from erp5.component.test.testSlapOSCloudConstraint import TestSlapOSConstraintMixin
from Products.ERP5Type.Base import WorkflowMethod
from erp5.component.test.SlapOSTestCaseMixin import withAbort

import transaction


class TestHostingSubscription(TestSlapOSConstraintMixin):

  # use decrator in order to avoid fixing consistency of new object
  @WorkflowMethod.disable
  def _createInstanceTree(self):
    self.subscription = self.portal.hosting_subscription_module.newContent(
        portal_type='Hosting Subscription')

  def afterSetUp(self):
    TestSlapOSConstraintMixin.afterSetUp(self)
    self._createInstanceTree()

  def beforeTearDown(self):
    transaction.abort()
    TestSlapOSConstraintMixin.beforeTearDown(self)

  def test_periodicity_hour_list_value(self):
    value = 7
    message = 'Attribute periodicity_hour_list value is [7] but should be [0]'
    self.assertNotIn(message, self.getMessageList(self.subscription))

    self.subscription.setPeriodicityHour(value)
    self.assertIn(message, self.getMessageList(self.subscription))

    self.subscription.setPeriodicityHour(0)

    self.assertFalse(any([
        q.startswith('Attribute periodicity_hour_list value is') \
        for q in self.getMessageList(self.subscription)]))

  def test_periodicity_minute_list_value(self):
    value = 7
    message = 'Attribute periodicity_minute_list value is [7] but should be [0]'
    self.assertNotIn(message, self.getMessageList(self.subscription))

    self.subscription.setPeriodicityMinute(value)
    self.assertIn(message, self.getMessageList(self.subscription))

    self.subscription.setPeriodicityMinute(0)

    self.assertFalse(any([
        q.startswith('Attribute periodicity_minute_list value is') \
        for q in self.getMessageList(self.subscription)]))

  def test_periodicity_month_day_list_lenght(self):
    message = 'There was too many objects in periodicity_month_day_list'
    self.assertNotIn(message, self.getMessageList(self.subscription))

    self.subscription.setPeriodicityMonthDayList([1, 2])
    self.assertIn(message, self.getMessageList(self.subscription))

    self.subscription.setPeriodicityMonthDayList([1])
    self.assertNotIn(message, self.getMessageList(self.subscription))

  def test_periodicity_month_day_value_range(self):
    message = 'The periodicity_month_day value is not between 1 and 28 '\
        'inclusive'
    self.assertNotIn(message, self.getMessageList(self.subscription))

    self.subscription.setPeriodicityMonthDay(0)
    self.assertIn(message, self.getMessageList(self.subscription))

    self.subscription.setPeriodicityMonthDay(29)
    self.assertIn(message, self.getMessageList(self.subscription))

    self.subscription.setPeriodicityMonthDay(28)
    self.assertNotIn(message, self.getMessageList(self.subscription))

    self.subscription.setPeriodicityMonthDay(1)
    self.assertNotIn(message, self.getMessageList(self.subscription))

    self.subscription.setPeriodicityMonthDay(15)
    self.assertNotIn(message, self.getMessageList(self.subscription))

    self.subscription.setPeriodicityMonthDay(None)
    self.assertNotIn(message, self.getMessageList(self.subscription))

  def test_periodicity_property(self):
    template = 'Property existence error for property %s, this '\
        'document has no such property or the property has never been set'
    self._test_property_existence(self.subscription, 'periodicity_hour',
      template % 'periodicity_hour', empty_string=False)
    self._test_property_existence(self.subscription, 'periodicity_minute',
      template % 'periodicity_minute', empty_string=False)
    self._test_property_existence(self.subscription, 'periodicity_month_day',
      template % 'periodicity_month_day', empty_string=False)

class TestSaleInvoiceTransaction(TestSlapOSConstraintMixin):
  @withAbort
  def _test_currency(self, invoice, setter, message):
    self.assertIn(message, self.getMessageList(invoice))

    currency = self.portal.currency_module.newContent(portal_type='Currency')
    setter(currency.getRelativeUrl())

    self.assertNotIn(message, self.getMessageList(invoice))

    resource = self.portal.service_module.newContent(portal_type='Service')
    setter(resource.getRelativeUrl())
    self.assertIn(message, self.getMessageList(invoice))

  def test_price_currency(self):
    invoice = self.portal.accounting_module.newContent(
        portal_type='Sale Invoice Transaction')
    message = "Arity Error for Relation ['price_currency'] and Type "\
        "('Currency',), arity is equal to 0 but should be between 1 and 1"
    self._test_currency(invoice, invoice.setPriceCurrency, message)

  def test_resource(self):
    invoice = self.portal.accounting_module.newContent(
        portal_type='Sale Invoice Transaction')
    message = "Arity Error for Relation ['resource'] and Type "\
        "('Currency',), arity is equal to 0 but should be between 1 and 1"
    self._test_currency(invoice, invoice.setResource, message)

  @withAbort
  def test_sale_invoice_specialise_sale_trade_condition_constraint(self):
    invoice = self.portal.accounting_module.newContent(
        portal_type='Sale Invoice Transaction')
    setter = invoice.setSpecialise
    message = "Arity Error for Relation ['specialise'] and Type "\
        "('Sale Trade Condition',), arity is equal to 0 but should be at least 1"
    self.assertNotIn(message, self.getMessageList(invoice))

    invoice = self.portal.accounting_module.newContent(
        portal_type='Sale Invoice Transaction',
        ledger='automated')
    setter = invoice.setSpecialise
    self.assertIn(message, self.getMessageList(invoice))

    sale_condition = self.portal.sale_trade_condition_module.newContent(
        portal_type='Sale Trade Condition')
    setter(sale_condition.getRelativeUrl())

    self.assertNotIn(message, self.getMessageList(invoice))

    purchase_condition = self.portal.purchase_trade_condition_module.newContent(
        portal_type='Purchase Trade Condition')
    setter(purchase_condition.getRelativeUrl())
    self.assertIn(message, self.getMessageList(invoice))

  @withAbort
  def test_specialise_value(self):
    invoice = self.portal.accounting_module.newContent(
        portal_type='Sale Invoice Transaction')
    message = "Arity Error for Relation ['specialise'] and Type " + \
      "('Sale Trade Condition',), arity is equal to 0 but should be at least 1"
    self.assertNotIn(message, self.getMessageList(invoice))

    invoice = self.portal.accounting_module.newContent(
        portal_type='Sale Invoice Transaction',
        ledger='automated')
    self.assertIn(message, self.getMessageList(invoice))

    sale_condition = self.portal.sale_trade_condition_module.newContent(
        portal_type='Sale Trade Condition')
    invoice.setSpecialise(sale_condition.getRelativeUrl())
    self.assertNotIn(message, self.getMessageList(invoice))

  @withAbort
  def test_total_price_equal_accounting(self):
    message = "Total price of invoice does not match accounting"
    invoice = self.portal.accounting_module.newContent(
        portal_type='Sale Invoice Transaction',
        price_currency='currency_module/EUR')
    invoice.newContent(portal_type='Invoice Line', quantity=1., price=1.)

    self.assertNotIn(message, self.getMessageList(invoice))
    self.portal.portal_workflow._jumpToStateFor(invoice, 'confirmed')
    self.assertIn(message, self.getMessageList(invoice))

    invoice.receivable.setQuantity(-1.0)
    invoice.income.setQuantity(1.0)
    self.assertNotIn(message, self.getMessageList(invoice))

  @withAbort
  def test_trade_model_match_lines(self):
    message = "Defined Trade Model does not match Lines definition"
    currency = self.portal.currency_module.EUR
    sale_trade_condition = self.portal.sale_trade_condition_module.newContent(
      portal_type="Sale Trade Condition",
      reference="Tax/payment for: %s" % currency.getRelativeUrl(),
      trade_condition_type="default",
      # XXX hardcoded
      specialise="business_process_module/slapos_sale_subscription_business_process",
      price_currency_value=currency,
      payment_condition_payment_mode='test-%s' % self.generateNewId()
    )
    sale_trade_condition.newContent(
      portal_type="Trade Model Line",
      reference="VAT",
      resource="service_module/slapos_tax",
      base_application="base_amount/invoicing/taxable",
      trade_phase="slapos/tax",
      price=0.2,
      quantity=1.0,
      membership_criterion_base_category=('price_currency', 'base_contribution'),
      membership_criterion_category=(
        'price_currency/%s' % currency.getRelativeUrl(),
        'base_contribution/base_amount/invoicing/taxable'
      )
    )
    sale_trade_condition.validate()
    invoice = self.portal.accounting_module.newContent(
        portal_type='Sale Invoice Transaction',
        price_currency_value=currency,
        ledger='automated',
        specialise_value=sale_trade_condition)
    invoice.newContent(portal_type='Invoice Line', quantity=1., price=1.,
        base_contribution='base_amount/invoicing/taxable')
    self.tic()

    self.assertNotIn(message, self.getMessageList(invoice))
    self.portal.portal_workflow._jumpToStateFor(invoice, 'confirmed')
    self.assertIn(message, self.getMessageList(invoice))

    invoice.newContent(portal_type='Invoice Line', quantity=1., price=.196,
        use='trade/tax',
        )
    self.assertNotIn(message, self.getMessageList(invoice))

  @withAbort
  def test_use_trade_sale_total_price_matches_delivery_constraint(self):
    message = "Total price does not match related Sale Packing List"
    currency = self.portal.currency_module.EUR
    sale_trade_condition = self.portal.sale_trade_condition_module.newContent(
      portal_type="Sale Trade Condition",
      reference="Tax/payment for: %s" % currency.getRelativeUrl(),
      trade_condition_type="default",
      # XXX hardcoded
      specialise="business_process_module/slapos_sale_subscription_business_process",
      price_currency_value=currency,
      payment_condition_payment_mode='test-%s' % self.generateNewId()
    )
    sale_trade_condition.newContent(
      portal_type="Trade Model Line",
      reference="VAT",
      resource="service_module/slapos_tax",
      base_application="base_amount/invoicing/taxable",
      trade_phase="slapos/tax",
      price=0.2,
      quantity=1.0,
      membership_criterion_base_category=('price_currency', 'base_contribution'),
      membership_criterion_category=(
        'price_currency/%s' % currency.getRelativeUrl(),
        'base_contribution/base_amount/invoicing/taxable'
      )
    )
    sale_trade_condition.validate()

    delivery = self.portal.sale_packing_list_module.newContent(
      portal_type='Sale Packing List')
    delivery.newContent(portal_type='Sale Packing List Line',
      use='trade/sale', quantity=1., price=1.)
    invoice = self.portal.accounting_module.newContent(
        portal_type='Sale Invoice Transaction',
        ledger="automated",
        specialise_value=sale_trade_condition)
    invoice_line = invoice.newContent(portal_type='Invoice Line', quantity=2.,
        price=1., use='trade/sale')

    self.assertNotIn(message, self.getMessageList(invoice))
    self.portal.portal_workflow._jumpToStateFor(invoice, 'confirmed')
    self.assertFalse(message in self.getMessageList(invoice))
    invoice.setCausalityValue(delivery)
    self.assertIn(message, self.getMessageList(invoice))
    invoice_line.setQuantity(1.)
    self.assertNotIn(message, self.getMessageList(invoice))
    invoice.newContent(portal_type='Invoice Line', quantity=2.,
        price=1.)
    self.assertNotIn(message, self.getMessageList(invoice))


class TestSalePackingList(TestSlapOSConstraintMixin):

  _portal_type = 'Sale Packing List'
  _line_portal_type = 'Sale Packing List Line'

  @withAbort
  def test_lines(self):
    message = 'Delivery Line is not defined'
    delivery = self.portal.getDefaultModule(self._portal_type).newContent(
        portal_type=self._portal_type)

    self.assertIn(message, self.getMessageList(delivery))
    delivery.newContent(portal_type=self._line_portal_type)
    self.assertNotIn(message, self.getMessageList(delivery))

  @withAbort
  def test_reference_not_empty(self):
    message = 'Reference must be defined'
    delivery = self.portal.getDefaultModule(self._portal_type).newContent(
        portal_type=self._portal_type)

    self.assertNotIn(message, self.getMessageList(delivery))
    delivery.setReference(None)
    self.assertIn(message, self.getMessageList(delivery))

  @withAbort
  def test_price_currency(self):
    message = 'Exactly one Currency shall be selected'
    delivery = self.portal.getDefaultModule(self._portal_type).newContent(
        portal_type=self._portal_type)
    self.assertIn(message, self.getMessageList(delivery))

    resource = self.portal.service_module.newContent(portal_type='Service')
    delivery.setPriceCurrency(resource.getRelativeUrl())
    self.assertIn(message, self.getMessageList(delivery))

    currency_1 = self.portal.currency_module.newContent(portal_type='Currency')
    currency_2 = self.portal.currency_module.newContent(portal_type='Currency')
    delivery.setPriceCurrencyList([currency_1.getRelativeUrl(),
      currency_2.getRelativeUrl()])
    self.assertIn(message, self.getMessageList(delivery))

    delivery.setPriceCurrency(currency_1.getRelativeUrl())
    self.assertNotIn(message, self.getMessageList(delivery))

  @withAbort
  def _test_category_arrow(self, category):
    message = "Arity Error for Relation ['%s'] and Type ('Organisation', "\
        "'Person'), arity is equal to 0 but should be between 1 and 1" % category
    message_2 = "Arity Error for Relation ['%s'] and Type ('Organisation', "\
        "'Person'), arity is equal to 2 but should be between 1 and 1" % category
    delivery = self.portal.getDefaultModule(self._portal_type).newContent(
        portal_type=self._portal_type)
    resource = self.portal.service_module.newContent(
        portal_type='Service').getRelativeUrl()
    person = self.portal.person_module.newContent(
        portal_type='Person').getRelativeUrl()
    organisation = self.portal.organisation_module.newContent(
        portal_type='Organisation').getRelativeUrl()

    key = '%s_list' % category
    self.assertIn(message, self.getMessageList(delivery))
    delivery.edit(**{key: [resource]})
    self.assertIn(message, self.getMessageList(delivery))
    delivery.edit(**{key: [person, organisation]})
    self.assertIn(message_2, self.getMessageList(delivery))
    delivery.edit(**{key: [person]})
    self.assertNotIn(message, self.getMessageList(delivery))
    self.assertNotIn(message_2, self.getMessageList(delivery))
    delivery.edit(**{key: [organisation]})
    self.assertNotIn(message, self.getMessageList(delivery))
    self.assertNotIn(message_2, self.getMessageList(delivery))

  def test_destination(self):
    self._test_category_arrow('destination')

  def test_destination_section(self):
    self._test_category_arrow('destination_section')

  def test_destination_decision(self):
    self._test_category_arrow('destination_decision')

  def test_source(self):
    self._test_category_arrow('source')

  @withAbort
  def test_specialise(self):
    category = 'specialise'
    message = "Arity Error for Relation ['%s'] and Type ('Sale Trade Condition"\
        "',), arity is equal to 0 but should be between 1 and 1" % category
    message_2 = "Arity Error for Relation ['%s'] and Type ('Sale Trade Condition"\
        "',), arity is equal to 2 but should be between 1 and 1" % category
    delivery = self.portal.getDefaultModule(self._portal_type).newContent(
        portal_type=self._portal_type)
    resource = self.portal.service_module.newContent(
        portal_type='Service').getRelativeUrl()
    stc_1 = self.portal.sale_trade_condition_module.newContent(
        portal_type='Sale Trade Condition').getRelativeUrl()
    stc_2 = self.portal.sale_trade_condition_module.newContent(
        portal_type='Sale Trade Condition').getRelativeUrl()

    key = '%s_list' % category
    self.assertIn(message, self.getMessageList(delivery))
    delivery.edit(**{key: [resource]})
    self.assertIn(message, self.getMessageList(delivery))
    delivery.edit(**{key: [stc_1, stc_2]})
    self.assertIn(message_2, self.getMessageList(delivery))
    delivery.edit(**{key: [stc_1]})
    self.assertNotIn(message, self.getMessageList(delivery))
    self.assertNotIn(message_2, self.getMessageList(delivery))

  @withAbort
  def test_start_date(self):
    message = 'Property start_date must be defined'
    delivery = self.portal.getDefaultModule(self._portal_type).newContent(
        portal_type=self._portal_type)
    self.assertIn(message, self.getMessageList(delivery))
    delivery.setStartDate('2012/01/01')
    self.assertNotIn(message, self.getMessageList(delivery))

class TestSalePackingListLine(TestSlapOSConstraintMixin):
  _portal_type = 'Sale Packing List'
  _line_portal_type = 'Sale Packing List Line'

  @withAbort
  def test_property_existence(self):
    message_quantity = 'No quantity defined'
    delivery_line = self.portal.getDefaultModule(self._portal_type).newContent(
        portal_type=self._portal_type).newContent(
        portal_type=self._line_portal_type)
    self.assertIn(message_quantity, self.getMessageList(delivery_line))
    delivery_line.setQuantity(1.0)
    self.assertNotIn(message_quantity, self.getMessageList(delivery_line))

  @withAbort
  def test_resource_arity(self):
    category = 'resource'
    message = "Arity Error for Relation ['%s'] and Type ('Data Operation', 'Service', 'Software Product'), arity is"\
        " equal to 0 but should be between 1 and 1" % category
    message_2 = "Arity Error for Relation ['%s'] and Type ('Data Operation', 'Service', 'Software Product'), arity is"\
        " equal to 2 but should be between 1 and 1" % category
    delivery_line = self.portal.getDefaultModule(self._portal_type).newContent(
        portal_type=self._portal_type).newContent(
        portal_type=self._line_portal_type)
    product = self.portal.product_module.newContent(
        portal_type='Product').getRelativeUrl()
    service_1 = self.portal.service_module.newContent(
        portal_type='Service').getRelativeUrl()
    service_2 = self.portal.service_module.newContent(
        portal_type='Service').getRelativeUrl()

    key = '%s_list' % category
    self.assertIn(message, self.getMessageList(delivery_line))
    delivery_line.edit(**{key: [product]})
    self.assertIn(message, self.getMessageList(delivery_line))
    delivery_line.edit(**{key: [service_1, service_2]})
    self.assertIn(message_2, self.getMessageList(delivery_line))
    delivery_line.edit(**{key: [service_1]})
    self.assertNotIn(message, self.getMessageList(delivery_line))
    self.assertNotIn(message_2, self.getMessageList(delivery_line))

class TestConsumptionDelivery(TestSalePackingList):
  _portal_type = 'Consumption Delivery'
  _line_portal_type = 'Consumption Delivery Line'

class TestConsumptionDeliveryLine(TestSalePackingListLine):
  _portal_type = 'Consumption Delivery'
  _line_portal_type = 'Consumption Delivery Line'

