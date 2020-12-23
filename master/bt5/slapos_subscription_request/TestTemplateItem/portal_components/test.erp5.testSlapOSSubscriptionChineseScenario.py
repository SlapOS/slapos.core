# -*- coding:utf-8 -*-
##############################################################################
#
# Copyright (c) 2019 Nexedi SA and Contributors. All Rights Reserved.
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

from erp5.component.test.testSlapOSSubscriptionScenario import TestSlapOSSubscriptionScenarioMixin
from erp5.component.test.SlapOSTestCaseMixin import changeSkin
from Products.ERP5Type.tests.utils import createZODBPythonScript

class TestSlapOSSubscriptionChineseScenarioMixin(TestSlapOSSubscriptionScenarioMixin):

  def afterSetUp(self):
    TestSlapOSSubscriptionScenarioMixin.afterSetUp(self)
    self.expected_individual_price_without_tax = 1573.3333333333335
    self.expected_individual_price_with_tax = 1888.00
    self.expected_reservation_fee = 188.00
    self.expected_reservation_fee_without_tax = 188
    self.expected_reservation_quantity_tax = 0
    self.expected_reservation_tax = 0
    self.expected_price_currency = "currency_module/CNY"
    self.normal_user = None
    self.expected_notification_language = "zh"


    self.login()
    self.createNotificationMessage("subscription_request-confirmation-with-password", language="zh",
      text_content='CHINESE! ${name} ${login_name} ${login_password}')
    self.createNotificationMessage("subscription_request-confirmation-without-password", language="zh",
                               text_content='CHINESE! ${name} ${login_name}')
    self.createNotificationMessage("subscription_request-instance-is-ready", language="zh",
      text_content='CHINESE! ${name} ${subscription_title} ${hosting_subscription_relative_url}')
    self.createNotificationMessage("subscription_request-payment-is-ready", language="zh",
      text_content='CHINESE! ${name} ${subscription_title} ${payment_relative_relative_url}')

  def _simulatePaymentTransaction_getVADSUrlDict(self):
    script_name = 'PaymentTransaction_getVADSUrlDict'
    if script_name in self.portal.portal_skins.custom.objectIds():
      raise ValueError('Precondition failed: %s exists in custom' % script_name)
    createZODBPythonScript(self.portal.portal_skins.custom,
                        script_name,
                        '*args, **kwargs',
                        '# Script body\n'
"""payment_transaction_url = context.getRelativeUrl()
return dict(vads_url_already_registered="%s/already_registered" % (payment_transaction_url),
  vads_url_cancel="%s/cancel" % (payment_transaction_url),
  vads_url_error="%s/error" % (payment_transaction_url),
  vads_url_referral="%s/referral" % (payment_transaction_url),
  vads_url_refused="%s/refused" % (payment_transaction_url),
  vads_url_success="%s/success" % (payment_transaction_url),
  vads_url_return="%s/return" % (payment_transaction_url),
)""")

  def _dropPaymentTransaction_getVADSUrlDict(self):
    script_name = 'PaymentTransaction_getVADSUrlDict'
    if script_name in self.portal.portal_skins.custom.objectIds():
      self.portal.portal_skins.custom.manage_delObjects(script_name)

  @changeSkin('Hal')
  def _requestSubscription(self, **kw):
    if self.cloud_invitation_token is not None:
      kw["token"] = self.cloud_invitation_token.getId()
    if 'target_language' not in kw:
      kw["target_language"] = "zh"
    kw["subscription_reference"] = self.subscription_condition.getReference().replace("_zh", "")

    original_mode = self.portal.portal_secure_payments.slapos_wechat_test.getWechatMode()
    self._simulatePaymentTransaction_getVADSUrlDict()
    try:
      self.portal.portal_secure_payments.slapos_wechat_test.setWechatMode("UNITTEST")
      self.logout()
      self.changeSkin('Hal')
      return self.web_site.hateoas.SubscriptionRequestModule_requestSubscription(**kw)
    finally:
      self._dropPaymentTransaction_getVADSUrlDict()
      self.portal.portal_secure_payments.slapos_wechat_test.setWechatMode(original_mode)

  def createSubscriptionCondition(self, slave=False):
    self.subscription_condition = self.portal.subscription_condition_module.newContent(
      portal_type="Subscription Condition",
      title="TestSubscriptionChineseScenario",
      short_tile="Test Your Chinese Scenario",
      description="This is a Chinese test",
      url_string=self.generateNewSoftwareReleaseUrl(),
      root_slave=slave,
      price=1888.00,
      price_currency="currency_module/CNY",
      default_source_reference="default",
      reference="rapidvm%s_zh" % self.new_id,
      # Aggregate and Follow up to web pages for product description and
      # Terms of service
      sla_xml='<?xml version="1.0" encoding="utf-8"?>\n<instance>\n</instance>',
      text_content='<?xml version="1.0" encoding="utf-8"?>\n<instance>\n</instance>',
      user_input={},
      source=self.expected_source,
      source_section=self.expected_source_section
    )
    self.subscription_condition.validate()
    self.subscription_condition.updateLocalRolesOnSecurityGroups()
    self.tic()

  def _payPayment(self, subscription_request):
    quantity = subscription_request.getQuantity()
    # Check Payment
    payment = self._getRelatedPaymentValue(subscription_request)

    self.assertEqual(self.expected_price_currency, payment.getPriceCurrency())
    self.assertEqual(-self.expected_reservation_fee*quantity,
      payment.PaymentTransaction_getTotalPayablePrice())
    
    self.assertEqual(payment.getSimulationState(), "started")

    # Pay 188 CNY per VM
    data_kw = {
        'result_code': 'SUCCESS',
        'trade_state': 'SUCCESS',
        'total_fee': self.expected_reservation_fee*100*quantity,
        'fee_type': 'CNY',
    }

    # Wechat_processUpdate will mark payment as payed by stopping it.
    payment.PaymentTransaction_createWechatEvent().WechatEvent_processUpdate(data_kw)
    return payment

  def checkAndPayFirstMonth(self, subscription_request):
    self.login()
    original_mode = self.portal.portal_secure_payments.slapos_wechat_test.getWechatMode()
    self._simulatePaymentTransaction_getVADSUrlDict()
    try:
      person = subscription_request.getDestinationSectionValue()

      quantity = subscription_request.getQuantity()
      self.portal.portal_secure_payments.slapos_wechat_test.setWechatMode("UNITTEST")
    
      self.login(person.getUserId())
      self.useWechatManually(self.web_site, person.getUserId(), is_email_expected=False)

      payment = self.portal.portal_catalog.getResultValue(
        portal_type="Payment Transaction",
        simulation_state="started")

      self.assertEqual(payment.getSourceSection(), self.expected_source_section)
      self.assertEqual(payment.getSourcePayment(), "%s/bank_account" % self.expected_source_section)

      authAmount = (int(self.expected_individual_price_with_tax*100)*1-int(self.expected_reservation_fee*100))*quantity

      self.assertEqual(int(payment.PaymentTransaction_getTotalPayablePrice()*100),
                     -authAmount)
    
      self.assertEqual(payment.getPriceCurrency(), self.expected_price_currency)

      self.logout()
      self.login()

      data_kw = {
        'result_code': 'SUCCESS',
        'trade_state': 'SUCCESS',
        'total_fee': authAmount,
        'fee_type': 'CNY',
      }

      # Wechat_processUpdate will mark payment as payed by stopping it.
      payment.PaymentTransaction_createWechatEvent().WechatEvent_processUpdate(data_kw)
    finally:
      self._dropPaymentTransaction_getVADSUrlDict()
      self.portal.portal_secure_payments.slapos_wechat_test.setWechatMode(original_mode)

  def checkAndPaySecondMonth(self, subscription_request):
    self.login()
    original_mode = self.portal.portal_secure_payments.slapos_wechat_test.getWechatMode()
    self._simulatePaymentTransaction_getVADSUrlDict()
    try:
      person = subscription_request.getDestinationSectionValue()

      quantity = subscription_request.getQuantity()
      self.portal.portal_secure_payments.slapos_wechat_test.setWechatMode("UNITTEST")
    
      self.login(person.getUserId())
      self.useWechatManually(self.web_site, person.getUserId())

      payment = self.portal.portal_catalog.getResultValue(
        portal_type="Payment Transaction",
        simulation_state="started")

      authAmount = int(self.expected_individual_price_with_tax*100)*quantity

      self.assertEqual(int(payment.PaymentTransaction_getTotalPayablePrice()*100),
                     -authAmount)
    
      self.assertEqual(payment.getPriceCurrency(), self.expected_price_currency)

      self.logout()
      self.login()

      data_kw = {
        'result_code': 'SUCCESS',
        'trade_state': 'SUCCESS',
        'total_fee': authAmount,
        'fee_type': 'CNY',
      }

      # Wechat_processUpdate will mark payment as payed by stopping it.
      payment.PaymentTransaction_createWechatEvent().WechatEvent_processUpdate(data_kw)
    finally:
      self._dropPaymentTransaction_getVADSUrlDict()
      self.portal.portal_secure_payments.slapos_wechat_test.setWechatMode(original_mode)



class TestSlapOSSubscriptionChineseScenario(TestSlapOSSubscriptionChineseScenarioMixin):

  def test_subscription_scenario_with_single_vm(self):
    self._test_subscription_scenario(amount=1)

  def test_subscription_with_3_vms_scenario(self):
    self._test_subscription_scenario(amount=3)

  def test_subscription_scenario_with_reversal_transaction(self):
    self._test_subscription_scenario_with_reversal_transaction(amount=1)

  def test_two_subscription_scenario(self):
    self._test_two_subscription_scenario(amount=1)

  def test_subscription_scenario_with_existing_user(self):
    self._test_subscription_scenario_with_existing_user(amount=1, language="zh")

  def test_subscription_scenario_with_existing_english_user(self):
    # Messages are in chinese, when subscribed via chinese website. Even if the english language is
    # english
    self._test_subscription_scenario_with_existing_user(amount=1, language="en")
