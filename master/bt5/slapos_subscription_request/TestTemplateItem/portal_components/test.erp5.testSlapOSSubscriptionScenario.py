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

from erp5.component.test.SlapOSTestCaseDefaultScenarioMixin import DefaultScenarioMixin
from erp5.component.test.SlapOSTestCaseMixin import changeSkin
from Products.ERP5Type.tests.utils import createZODBPythonScript

from DateTime import DateTime
import datetime

class TestSlapOSSubscriptionScenarioMixin(DefaultScenarioMixin):

  def afterSetUp(self):
    self.unpinDateTime()
    self.normal_user = None
    self.expected_individual_price_without_tax = 195
    self.expected_individual_price_with_tax = 234
    self.expected_reservation_fee = 30.00
    self.expected_reservation_fee_without_tax = 25
    self.expected_reservation_quantity_tax = 25
    self.expected_reservation_tax = 5.0
    self.expected_price_currency = "currency_module/EUR"
 

    self.expected_zh_individual_price_without_tax = 1888
    self.expected_zh_individual_price_with_tax = 1888
    self.expected_zh_reservation_fee = 188.00
    self.expected_zh_reservation_fee_without_tax = 188
    self.expected_zh_reservation_quantity_tax = 188
    self.expected_zh_reservation_tax = 0
 
    self.expected_notification_language = "en"
    self.expected_source = self.expected_slapos_organisation
    self.expected_source_section = self.expected_slapos_organisation
    self.cloud_invitation_token = None
    self.resource_variation_reference = None
    self.expected_free_reservation = 0
    self.non_subscription_related_instance_amount = 0
    self.skip_destroy_and_check = 0

    self.login()
    self.portal.portal_alarms.slapos_subscription_request_process_draft.setEnabled(True)
    self.portal.portal_alarms.slapos_subscription_request_process_ordered.setEnabled(True)
    self.portal.portal_alarms.slapos_subscription_request_process_planned.setEnabled(True)
    self.portal.portal_alarms.slapos_subscription_request_process_confirmed.setEnabled(True)
    self.portal.portal_alarms.slapos_subscription_request_process_started.setEnabled(True)

    DefaultScenarioMixin.afterSetUp(self)

    self.portal.accounting_module.\
      template_pre_payment_subscription_sale_invoice_transaction.\
      updateLocalRolesOnSecurityGroups()

    self.portal.accounting_module.\
      slapos_pre_payment_template.\
       updateLocalRolesOnSecurityGroups()

    # One user to create compute_nodes to deploy the subscription
    self.createAdminUser()
    self.cleanUpNotificationMessage()
    self.portal.portal_catalog.searchAndActivate(
      portal_type='Active Process',
      method_id='ActiveProcess_deleteSelf')
    self.tic()
    
    self.createNotificationMessage("subscription_request-confirmation-with-password")
    self.createNotificationMessage("subscription_request-confirmation-without-password",
                               text_content='${name} ${login_name}')
    self.createNotificationMessage("subscription_request-instance-is-ready", 
      text_content='${name} ${subscription_title} ${instance_tree_relative_url}')
    self.createNotificationMessage("subscription_request-payment-is-ready",
      text_content='${name} ${subscription_title} ${payment_relative_relative_url}')
    
    self.createNotificationMessage("subscription_request-confirmation-with-password", language="zh",
      text_content='CHINESE! ${name} ${login_name} ${login_password}')
    self.createNotificationMessage("subscription_request-confirmation-without-password", language="zh",
                               text_content='CHINESE! ${name} ${login_name}')
    self.createNotificationMessage("subscription_request-instance-is-ready", language="zh",
      text_content='CHINESE! ${name} ${subscription_title} ${instance_tree_relative_url}')
    self.createNotificationMessage("subscription_request-payment-is-ready", language="zh",
      text_content='CHINESE! ${name} ${subscription_title} ${payment_relative_relative_url}')

    self.cleanUpSubscriptionRequest()
    self.tic()
    
    self.login()
    self.createSubscriptionCondition()

    # some preparation
    self.logout()
    self.web_site = self.portal.web_site_module.hostingjs


  # The PaymentTransaction_getVADSUrlDict is required by the implementation
  # wechat payments.
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


  def cleanUpSubscriptionRequest(self):
    for subscription_request in self.portal.portal_catalog(
      portal_type="Subscription Request",
      simulation_state=["draft", "planned", "ordered", "confirmed"],
      title="Test Subscription Request %"):
      if subscription_request.getSimulationState() == "draft":
        subscription_request.cancel()
      if subscription_request.getSimulationState() == "planned":
        subscription_request.order()
      if subscription_request.getSimulationState() == "ordered":
        subscription_request.confirm()
      if subscription_request.getSimulationState() == "confirmed":
        subscription_request.start()
      if subscription_request.getSimulationState() == "started":
        subscription_request.stop()

  def cleanUpNotificationMessage(self):
    for notification_message in self.portal.portal_catalog(
      portal_type="Notification Message",
      validation_state=["validated"],
      title="TestSubscriptionSkins %"):
      if str(notification_message.getVersion("")) == "999":
        notification_message.invalidate()

  def createNotificationMessage(self, reference,
      content_type='text/html', language="en", text_content='${name} ${login_name} ${login_password}'):

    notification_message = self.portal.notification_message_module.newContent(
      portal_type="Notification Message",
      text_content_substitution_mapping_method_id='NotificationMessage_getSubstitutionMappingDictFromArgument',
      title='TestSubscriptionSkins Notification Message %s %s' % (language, reference),
      text_content=text_content,
      content_type=content_type,
      reference=reference,
      version=999,
      language=language
      )
    notification_message.validate()
    return notification_message

  def createAdminUser(self):
    """ Create a Admin user, to manage compute_nodes and instances eventually """
    admin_user_login = self.portal.portal_catalog.getResultValue(
      portal_type="ERP5 Login",
      reference="admin_user",
      validation_state="validated"
    )

    if admin_user_login is None:
      admin_user = self.portal.person_module.template_member.\
                                 Base_createCloneDocument(batch_mode=1)

      admin_user.newContent(
        portal_type="ERP5 Login",
        reference="admin_user").validate()

      admin_user.edit(
        first_name="Admin User",
        reference="Admin_user",
        default_email_text="do_not_reply_to_admin@example.org",
      )

      for assignment in admin_user.contentValues(portal_type="Assignment"):
        assignment.open()

      admin_user.validate()
      self.admin_user = admin_user
    else:
      self.admin_user = admin_user_login.getParentValue()

  def createNormalUser(self, email, name, language):
    """ Create a Normal user """
    normal_user_login = self.portal.portal_catalog.getResultValue(
      portal_type="ERP5 Login",
      reference=email,
      validation_state="validated"
    )

    if normal_user_login is None:
      normal_user = self.portal.person_module.template_member.\
                                 Base_createCloneDocument(batch_mode=1)

      normal_user.newContent(
        portal_type="ERP5 Login",
        reference=email).validate()

      normal_user.edit(
        first_name=name,
        reference=email,
        default_email_text=email,
      )

      for assignment in normal_user.contentValues(portal_type="Assignment"):
        assignment.open()

      normal_user.validate()
      self.normal_user = normal_user
    else:
      self.normal_user = normal_user_login.getParentValue()
    self.normal_user.setLanguage(language)

  def createChineseSubscriptionCondition(self, slave=False):
    subscription_condition = self.portal.subscription_condition_module.newContent(
      portal_type="Subscription Condition",
      title="TestSubscriptionChineseScenario",
      short_tile="Test Your Chinese Scenario",
      description="This is a Chinese test",
      url_string=self.generateNewSoftwareReleaseUrl(),
      root_slave=slave,
      price=self.expected_zh_individual_price_with_tax,
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
    subscription_condition.validate()
    subscription_condition.updateLocalRolesOnSecurityGroups()
    self.tic()
    return subscription_condition

  def createSubscriptionCondition(self, slave=False):
    self.subscription_condition = self.portal.subscription_condition_module.newContent(
      portal_type="Subscription Condition",
      title="TestSubscriptionScenario",
      short_tile="Test Your Scenario",
      description="This is a test",
      url_string=self.generateNewSoftwareReleaseUrl(),
      root_slave=slave,
      price=self.expected_individual_price_with_tax,
      price_currency="currency_module/EUR",
      default_source_reference="default",
      reference="rapidvm%s" % self.new_id,
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

  def getSubscriptionRequest(self, email, subscription_condition):
    subscription_request_list = subscription_condition.getSpecialiseRelatedValueList(
              portal_type='Subscription Request')
    self.assertEqual(len(subscription_request_list), 1)
    return subscription_request_list[0]

  def getSubscriptionRequestList(self, email, subscription_condition):
    subscription_request_list = subscription_condition.getSpecialiseRelatedValueList(
              portal_type='Subscription Request')
    return subscription_request_list

  def checkSubscriptionRequest(self, subscription_request, email, subscription_condition):
    self.assertNotEqual(subscription_request, None)
    self.assertEqual(subscription_request.getDefaultEmailText(), email)
    self.assertEqual(subscription_request.getUrlString(), subscription_condition.getUrlString())
    self.assertEqual(subscription_request.getRootSlave(), subscription_condition.getRootSlave())
    self.assertEqual(subscription_request.getTextContent(),
      '<?xml version="1.0" encoding="utf-8"?>\n<instance>\n</instance>')
    #self.assertEqual(trial_request.getSlaXml(), '<?xml version="1.0" encoding="utf-8"?>\n<instance>\n</instance>')
    self.assertEqual(subscription_request.getSourceReference(), "default")

  def checkDraftSubscriptionRequest(self, subscription_request, email, subscription_condition,
                                       amount=1):
    self.checkSubscriptionRequest(subscription_request, email, subscription_condition)
    # XXX This might be diferent
    self.assertEqual(subscription_request.getQuantity(), amount)

    self.assertEqual(subscription_request.getAggregate(), None)
    invoice = subscription_request.getCausalityValue(portal_type="Sale Invoice Transaction")
    self.assertNotEqual(invoice, None)
    payment = invoice.getCausalityRelatedValue(portal_type="Payment Transaction")
    self.assertNotEqual(payment, None)

  def checkPlannedSubscriptionRequest(self, subscription_request, email,
                                            subscription_condition):
    self.checkSubscriptionRequest(subscription_request, email,
                                  subscription_condition)
    self.assertEqual(subscription_request.getSimulationState(), "planned")

  def checkOrderedSubscriptionRequest(self, subscription_request, email,
                subscription_condition, 
                notification_message="subscription_request-confirmation-with-password"):
    self.checkSubscriptionRequest(subscription_request, email,
                                  subscription_condition)
    self.assertEqual(subscription_request.getSimulationState(), "ordered")
    self.checkBootstrapUser(subscription_request)
    self.checkEmailNotification(subscription_request, notification_message)

  def checkConfirmedSubscriptionRequest(self, subscription_request, email,
                      subscription_condition, 
                      notification_message="subscription_request-payment-is-ready"):
    self.checkSubscriptionRequest(subscription_request, email,
                                  subscription_condition)
    invoice = subscription_request.SubscriptionRequest_verifyPaymentBalanceIsReady()
    self.assertNotEqual(invoice, None)
    self.assertEqual(invoice.getSimulationState(), 'stopped')

    # Assert instance is allocated and without error
    self.assertEqual(True,
      subscription_request.SubscriptionRequest_verifyInstanceIsAllocated(verbose=True))

    self.assertEqual(subscription_request.getSimulationState(), "confirmed",
      "%s != confirmed (%s)" % (subscription_request.getSimulationState(),
                                subscription_request.SubscriptionRequest_processOrdered()))

    self.checkEmailPaymentNotification(subscription_request, notification_message)

  def checkStartedSubscriptionRequest(self, subscription_request, email,
                        subscription_condition, 
                        notification_message="subscription_request-instance-is-ready"):
    self.checkSubscriptionRequest(subscription_request, email,
                                  subscription_condition)
    self.assertEqual(subscription_request.getSimulationState(), "started")
    self.checkEmailInstanceNotification(subscription_request, notification_message)

  def checkStoppedSubscriptionRequest(self, subscription_request, email,
                        subscription_condition):
    self.checkSubscriptionRequest(subscription_request, email,
                                  subscription_condition)
    self.assertEqual(subscription_request.getSimulationState(), "stopped")

  def _getRelatedPaymentValue(self, subscription_request):
    invoice = subscription_request.getCausalityValue(portal_type="Sale Invoice Transaction")
    return invoice.getCausalityRelatedValue(portal_type="Payment Transaction")

  def createReversalInvoiceAndCancelPayment(self, subscription_request):
    self.login()
    person = subscription_request.getDestinationSectionValue()
    self.login(person.getUserId())

    invoice_list = person.Entity_getOutstandingAmountList()
    self.assertEqual(len(invoice_list), 1)
    sale_transaction_invoice = invoice_list[0].getObject()

    self.logout()
    self.login()
    sale_transaction_invoice.SaleInvoiceTransaction_createReversalSaleInvoiceTransaction(batch_mode=1)

  def checkSubscriptionRequestPayment(self, subscription_request, authAmount):

    if subscription_request.getSource() is not None:
      self.assertNotEqual(subscription_request.getSourceSection(), None)
      self.assertNotEqual(subscription_request.getSource(), None)
      #expected_source = subscription_request.getSource()
      expected_source_section = subscription_request.getSourceSection()
    else:
      self.assertEqual(subscription_request.getSourceSection(), None)
      self.assertEqual(subscription_request.getSource(), None)
      #expected_source = self.expected_source
      expected_source_section = self.expected_source_section

    # Be accurate when select the payment
    payment = self.portal.portal_catalog.getResultValue(
      portal_type="Payment Transaction",
      destination_section_uid=subscription_request.getDestinationSectionUid(),
      source_section_uid=self.portal.restrictedTraverse(expected_source_section).getUid(),
      simulation_state="started")

    self.assertEqual(payment.getSourceSection(),
      expected_source_section)
    self.assertEqual(payment.getSourcePayment(),
      "%s/bank_account" % expected_source_section)

    self.assertEqual(int(round(payment.PaymentTransaction_getTotalPayablePrice(), 2)*100),
                     -authAmount)
    
    self.assertEqual(payment.getPriceCurrency(),
        subscription_request.getPriceCurrency())

    # Check related invoice Data
    invoice_list = payment.getCausalityValueList()
    self.assertEqual(len(invoice_list), 1)

    invoice = invoice_list[0]

    delivery_list = invoice.getCausalityValueList()
    # Invoices related to Subscription Request don't merge
    self.assertEqual(len(delivery_list), 1)
    sale_packing_list = delivery_list[0]

    subscription_delivery_line_list = self.portal.portal_catalog(
      portal_type="Sale Packing List Line",
      default_resource_uid=self.portal.service_module.slapos_instance_subscription.getUid(),
      grouping_reference=sale_packing_list.getReference()
    )

    self.assertEqual(len(subscription_delivery_line_list), 1, 
      "len(%s) is not 1" % [i.getObject() for i in subscription_delivery_line_list])
    # Check more :)
    
    return payment

  def checkAndPayFirstMonth(self, subscription_request):
    self.login()
    person = subscription_request.getDestinationSectionValue()

    quantity = subscription_request.getQuantity()
    self.login(person.getUserId())
    self.usePaymentManually(
      self.web_site,
      person.getUserId(),
      is_email_expected=False, 
      subscription_request=subscription_request)

    self.logout()
    self.login()

    # 195 is the month payment
    # 195*1 is the 1 months to pay upfront to use.
    # 25 is the reservation fee deduction.
    authAmount = (int(self.expected_individual_price_with_tax*100)*1-int(self.expected_reservation_fee*100))*quantity
    payment = self.checkSubscriptionRequestPayment(subscription_request, authAmount)

    data_kw = {
      "status": "SUCCESS",
      "answer": {
        "transactions": [
          {
            "detailedStatus": "AUTHORISED",
            "transactionDetails": {
              "cardDetails": {
                "authorizationResponse": {
                  "amount": authAmount,
                  "currency": "EUR",
                },
              },
            },
          }
        ],
      },
    }
    payment.PaymentTransaction_createPayzenEvent().PayzenEvent_processUpdate(data_kw)

  def checkAndPaySecondMonth(self, subscription_request):
    self.login()
    person = subscription_request.getDestinationSectionValue()

    quantity = subscription_request.getQuantity()
    self.login(person.getUserId())
    self.usePaymentManually(
      self.web_site,
      person.getUserId(),
      subscription_request=subscription_request)

    self.logout()
    self.login()

    authAmount = int(self.expected_individual_price_with_tax*100)*quantity
    payment = self.checkSubscriptionRequestPayment(subscription_request, authAmount)

    data_kw = {
      "status": "SUCCESS",
      "answer": {
        "transactions": [
          {
            "detailedStatus": "AUTHORISED",
            "transactionDetails": {
              "cardDetails": {
                "authorizationResponse": {
                  "amount": authAmount,
                  "currency": "EUR",
                },
              },
            },
          }
        ],
      },
    }
    payment.PaymentTransaction_createPayzenEvent().PayzenEvent_processUpdate(data_kw)

  def checkAndPayFirstMonthViaWechat(self, subscription_request):
    self.login()
    original_mode = self.portal.portal_secure_payments.slapos_wechat_test.getWechatMode()
    self._simulatePaymentTransaction_getVADSUrlDict()
    try:
      person = subscription_request.getDestinationSectionValue()

      quantity = subscription_request.getQuantity()
      self.portal.portal_secure_payments.slapos_wechat_test.setWechatMode("UNITTEST")
    
      self.login(person.getUserId())
      self.usePaymentManually(
        self.web_site,
        person.getUserId(),
        is_email_expected=False,
        subscription_request=subscription_request)

      self.logout()
      self.login()

      authAmount = (int(self.expected_zh_individual_price_with_tax*100)*1-int(self.expected_zh_reservation_fee*100))*quantity
      payment = self.checkSubscriptionRequestPayment(subscription_request, authAmount)

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

  def checkAndPaySecondMonthViaWechat(self, subscription_request):
    self.login()
    original_mode = self.portal.portal_secure_payments.slapos_wechat_test.getWechatMode()
    self._simulatePaymentTransaction_getVADSUrlDict()
    try:
      person = subscription_request.getDestinationSectionValue()

      quantity = subscription_request.getQuantity()
      self.portal.portal_secure_payments.slapos_wechat_test.setWechatMode("UNITTEST")
    
      self.login(person.getUserId())
      self.usePaymentManually(
        self.web_site,
        person.getUserId(),
        subscription_request=subscription_request)

      self.logout()
      self.login()

      authAmount = int(self.expected_zh_individual_price_with_tax*100)*quantity
      payment = self.checkSubscriptionRequestPayment(subscription_request, authAmount)

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

  def _checkFreeReservationPayment(self, subscription_request):
    quantity = subscription_request.getQuantity()
    # Check Payment
    payment = self._getRelatedPaymentValue(subscription_request)

    self.assertEqual(subscription_request.getPriceCurrency(),
      payment.getPriceCurrency())
    self.assertEqual(-self.expected_reservation_fee*quantity,
      payment.PaymentTransaction_getTotalPayablePrice())
    
    self.assertEqual(payment.getSimulationState(), "stopped")
    return payment

  def _payPayment(self, subscription_request):
    quantity = subscription_request.getQuantity()
    # Check Payment
    payment = self._getRelatedPaymentValue(subscription_request)

    self.assertEqual(subscription_request.getPriceCurrency(),
      payment.getPriceCurrency())
    self.assertEqual(payment.getSimulationState(), "started")

    # Pay with appropriate mode depending of the currency. 
    if payment.getPriceCurrency() == "currency_module/CNY":
      self.assertEqual(-round(self.expected_zh_reservation_fee*quantity, 2),
        round(payment.PaymentTransaction_getTotalPayablePrice(), 2))
    
      # Pay 188 CNY per VM
      data_kw = {
        'result_code': 'SUCCESS',
        'trade_state': 'SUCCESS',
        'total_fee': self.expected_zh_reservation_fee*100*quantity,
        'fee_type': 'CNY',
      }

      # Wechat_processUpdate will mark payment as payed by stopping it.
      payment.PaymentTransaction_createWechatEvent().WechatEvent_processUpdate(data_kw)
    else:
      self.assertEqual(-round(self.expected_reservation_fee*quantity, 2),
        round(payment.PaymentTransaction_getTotalPayablePrice(), 2))
    
      # Pay 25 euros per VM
      data_kw = {
        "status": "SUCCESS",
        "answer": {
          "transactions": [
            {
              "detailedStatus": "AUTHORISED",
              "transactionDetails": {
                "cardDetails": {
                  "authorizationResponse": {
                    "amount": self.expected_reservation_fee*100*quantity,
                    "currency": "EUR",
                  },
                },
              },
            }
          ],
        },
      }
      # Payzen_processUpdate will mark payment as payed by stopping it.
      payment.PaymentTransaction_createPayzenEvent().PayzenEvent_processUpdate(data_kw)
    return payment

  def checkAndPaySubscriptionPayment(self, subscription_request_list):
    for subscription_request in subscription_request_list:
      quantity = subscription_request.getQuantity()
      invoice = subscription_request.getCausalityValue(
        portal_type="Sale Invoice Transaction")

      self.assertEqual(invoice.getSimulationState(), "confirmed")
      self.assertEqual(invoice.getCausalityState(), "building")

      if subscription_request.getSpecialiseValue().getSource() is not None:
        self.assertNotEqual(subscription_request.getSourceSection(), None)
        self.assertNotEqual(subscription_request.getSource(), None)

        expected_source = subscription_request.getSource()
        expected_source_section = subscription_request.getSourceSection()
      else:
        self.assertEqual(subscription_request.getSourceSection(), None)
        self.assertEqual(subscription_request.getSource(), None)
        expected_source = self.expected_source
        expected_source_section = self.expected_source_section

      self.assertEqual(invoice.getSource(), expected_source)
      self.assertEqual(invoice.getSourceSection(), expected_source_section)

      # Pay Invoice if it is not Free
      if not self.expected_free_reservation:
        payment = self._payPayment(subscription_request)
      else:
        payment = self._checkFreeReservationPayment(subscription_request)

      # Check Payment
      self.assertEqual(payment.getSourceSection(), expected_source_section)
      self.assertEqual(payment.getSourcePayment(),
                       "%s/bank_account" % expected_source_section)

      self.tic()
      self.assertEqual(payment.getSimulationState(), "stopped")

    # stabilise aggregated invoices and expand them
    self.stepCallSlaposManageBuildingCalculatingDeliveryAlarm()
    self.tic()

    # update invoices with their tax & discount
    self.stepCallSlaposTriggerBuildAlarm()
    self.tic()
    self.stepCallSlaposManageBuildingCalculatingDeliveryAlarm()
    self.tic()

    # update invoices with their tax & discount transaction lines
    self.stepCallSlaposTriggerBuildAlarm()
    self.tic()
    self.stepCallSlaposManageBuildingCalculatingDeliveryAlarm()
    self.tic()

    # stop the invoices and solve them again
    self.stepCallSlaposStopConfirmedAggregatedSaleInvoiceTransactionAlarm()
    self.tic()
    self.stepCallSlaposManageBuildingCalculatingDeliveryAlarm()
    self.tic()

    for subscription_request in subscription_request_list:
      invoice = subscription_request.getCausalityValue(
        portal_type="Sale Invoice Transaction")

      if subscription_request.getPriceCurrency() == "currency_module/CNY":
        expected_reservation_fee_without_tax = self.expected_zh_reservation_fee_without_tax
        expected_reservation_quantity_tax = self.expected_zh_reservation_quantity_tax
        expected_reservation_tax = self.expected_zh_reservation_tax
        expected_reservation_fee = self.expected_zh_reservation_fee
      else:
        expected_reservation_fee_without_tax = self.expected_reservation_fee_without_tax
        expected_reservation_quantity_tax = self.expected_reservation_quantity_tax
        expected_reservation_tax = self.expected_reservation_tax
        expected_reservation_fee = self.expected_reservation_fee

      self.assertEqual(invoice.getSimulationState(), "stopped", invoice.getRelativeUrl())
      self.assertEqual(invoice.getCausalityState(), "solved")
      self.assertEqual(invoice.getPriceCurrency(),
        subscription_request.getPriceCurrency())
      for line in invoice.objectValues():
        if line.getResource() == "service_module/slapos_reservation_fee":
          self.assertEqual(line.getTotalQuantity(), quantity)
          if self.expected_free_reservation:
            self.assertEqual(round(line.getTotalPrice(), 2),  0.0)
          else:
            self.assertEqual(round(line.getTotalPrice(), 2),
              round(expected_reservation_fee_without_tax*quantity, 2))
        if line.getResource() == "service_module/slapos_tax":
          self.assertEqual(round(line.getTotalQuantity(), 2),
                           round(expected_reservation_quantity_tax*quantity, 2))
          self.assertEqual(round(line.getTotalPrice(), 2),
                           round(expected_reservation_tax*quantity, 2))

      self.assertEqual(round(invoice.getTotalPrice(), 2),
                       round(expected_reservation_fee*quantity, 2))

  def checkSecondMonthAggregatedSalePackingList(self, subscription_request, sale_packing_list):
    sale_packing_list_line = [ i for i in sale_packing_list.objectValues()
      if i.getResource() == "service_module/slapos_instance_subscription"][0]

    quantity = subscription_request.getQuantity()
    # The values are without tax
    if subscription_request.getPriceCurrency() == "currency_module/CNY":
      expected_individual_price_without_tax = self.expected_zh_individual_price_without_tax
    else:
      expected_individual_price_without_tax = self.expected_individual_price_without_tax

    self.assertEqual(sale_packing_list_line.getQuantity(), 1*quantity)
    self.assertEqual(round(sale_packing_list_line.getPrice(), 2),
      round(expected_individual_price_without_tax, 2))
    self.assertEqual(round(sale_packing_list_line.getTotalPrice(), 2), 
      round(1*expected_individual_price_without_tax*quantity, 2))

    self.assertEqual(sale_packing_list.getCausality(),
                     subscription_request.getRelativeUrl())

    self.assertEqual(sale_packing_list.getCausality(),
                     subscription_request.getRelativeUrl())

    self.assertEqual(sale_packing_list.getPriceCurrency(),
                     subscription_request.getPriceCurrency())

  def _checkSecondMonthSimulation(self, subscription_request_list,
          default_email_text, subscription_server):

    # Needed?  
    self.simulateSlapgridCP(subscription_server)
    self.tic()

    self.stepCallSlaposUpdateOpenSaleOrderPeriodAlarm()
    self.tic()

    for subscription_request in subscription_request_list:
      self.checkAllocationOnRelatedInstance(subscription_request)

    # Needed?  
    self.simulateSlapgridCP(subscription_server)
    self.tic()

    # generate simulation for open order
    self.stepCallUpdateOpenOrderSimulationAlarm(full=1)
    self.tic()

    # build subscription packing list
    self.stepCallSlaposTriggerBuildAlarm()
    self.tic()

    # stabilise build deliveries and expand them
    self.stepCallSlaposManageBuildingCalculatingDeliveryAlarm()
    self.tic()

    # build aggregated packing list
    self.stepCallSlaposTriggerAggregatedDeliveryOrderBuilderAlarm()
    self.tic()

    # stabilise aggregated deliveries and expand them
    self.stepCallSlaposManageBuildingCalculatingDeliveryAlarm()
    self.tic()

    # check if Packing list is generated with the right trade condition
    preference_tool = self.portal.portal_preferences
    aggregate_subscription_condition = \
      preference_tool.getPreferredAggregatedSubscriptionSaleTradeCondition()
    trade_condition = preference_tool.getPreferredAggregatedSaleTradeCondition()

    for subscription_request in subscription_request_list:
      sale_packing_list_list = self.getAggregatedSalePackingList(
        subscription_request, aggregate_subscription_condition)
      if not len(sale_packing_list_list):
        diverged_sale_packing_list_list = self.getDivergedAggregatedSalePackingList(
          subscription_request, aggregate_subscription_condition)
        self.assertEqual(0, len(diverged_sale_packing_list_list))

      self.assertEqual(1, len(sale_packing_list_list))

      self.checkSecondMonthAggregatedSalePackingList(subscription_request, sale_packing_list_list[0])

      expected_sale_packing_list_amount = (len(subscription_request_list) * 2)+\
        self.non_subscription_related_instance_amount

      self.assertEqual(expected_sale_packing_list_amount, 
        len(self.getSubscriptionSalePackingList(subscription_request)))

      self.assertEqual(0, len(self.getAggregatedSalePackingList(
        subscription_request, trade_condition)))

    # Call this alarm shouldn't affect the delivery
    self.stepCallSlaposStartConfirmedAggregatedSalePackingListAlarm(
        accounting_date=DateTime('2222/01/01'))
    self.tic()

    for subscription_request in subscription_request_list:
      self.assertEqual(1, len(self.getAggregatedSalePackingList(
        subscription_request, aggregate_subscription_condition)))

    # Call this alarm shouldn't affect the delivery
    self.stepCallSlaposStartConfirmedAggregatedSubscriptionSalePackingListAlarm()
    self.tic()

    for subscription_request in subscription_request_list:
      self.assertEqual(0, len(self.getAggregatedSalePackingList(
        subscription_request, trade_condition)))

    # stabilise aggregated deliveries and expand them
    self.stepCallSlaposManageBuildingCalculatingDeliveryAlarm()
    self.tic()

    # deliver aggregated deliveries
    self.stepCallSlaposDeliverStartedAggregatedSalePackingListAlarm()
    self.tic()

    # stabilise aggregated deliveries and expand them
    self.stepCallSlaposManageBuildingCalculatingDeliveryAlarm()
    self.tic()

    # build aggregated invoices
    self.stepCallSlaposTriggerBuildAlarm()
    self.tic()

    # stabilise aggregated invoices and expand them
    self.stepCallSlaposManageBuildingCalculatingDeliveryAlarm()
    self.tic()

    # update invoices with their tax & discount
    self.stepCallSlaposTriggerBuildAlarm()
    self.tic()
    self.stepCallSlaposManageBuildingCalculatingDeliveryAlarm()
    self.tic()

    # update invoices with their tax & discount transaction lines
    self.stepCallSlaposTriggerBuildAlarm()
    self.tic()
    self.stepCallSlaposManageBuildingCalculatingDeliveryAlarm()
    self.tic()

    # stop the invoices and solve them again
    self.stepCallSlaposStopConfirmedAggregatedSaleInvoiceTransactionAlarm()
    self.tic()
    self.stepCallSlaposManageBuildingCalculatingDeliveryAlarm()
    self.tic()

    # trigger the CRM interaction
    self.stepCallSlaposCrmCreateRegularisationRequestAlarm()
    self.tic()

    # Test if balance is bad now
    subscriber = subscription_request.getDestinationSectionValue()

    
    if subscription_request.getPriceCurrency() == "currency_module/CNY":
      expected_individual_price_with_tax = self.expected_zh_individual_price_with_tax
    else:
      expected_individual_price_with_tax = self.expected_individual_price_with_tax
    expected_amount = round(expected_individual_price_with_tax*sum([i.getQuantity(0)
     for i in subscription_request_list]),2)

    # We generate now after the debt is active
    self.assertEqual(round(subscriber.Entity_statOutstandingAmount(at_date=DateTime()), 2), expected_amount)
    self.assertEqual(round(subscriber.Entity_statOutstandingAmount(), 2), expected_amount)

    # Invoice to Pay
    self.assertEqual(
      round(subscriber.Entity_statSlapOSOutstandingAmount(at_date=DateTime()+20), 2),
      expected_amount)

    # Pay this new invoice
    for subscription_request in subscription_request_list:
      if subscription_request.getPriceCurrency() == "currency_module/CNY":
        self.checkAndPaySecondMonthViaWechat(subscription_request)
      else:
        self.checkAndPaySecondMonth(subscription_request)
      self.tic()

    # Here the invoice was payed before the date, so value is negative. 
    self.assertEqual(round(subscriber.Entity_statOutstandingAmount(at_date=DateTime()), 2),
      0.0)

    self.assertEqual(round(subscriber.Entity_statOutstandingAmount(), 2), 0.0)

    # All payed
    self.assertEqual(
      round(subscriber.Entity_statSlapOSOutstandingAmount(at_date=DateTime()+20), 2),
      0.0)

  def checkBootstrapUser(self, subscription_request):
    person = subscription_request.getDestinationSectionValue(portal_type="Person")
    self.assertEqual(person.getDefaultEmailText(),
                     subscription_request.getDefaultEmailText())
    self.assertEqual(person.getValidationState(), "validated")

    login_list = [x for x in person.objectValues(portal_type='ERP5 Login') \
              if x.getValidationState() == 'validated']

    self.assertEqual(len(login_list), 1)
    self.assertEqual(login_list[0].getReference(), person.getDefaultEmailText())
    self.assertSameSet(person.getRoleList(), ["member", "subscriber"])

  def checkEmailNotification(self, subscription_request,
                 notification_message="subscription_request-confirmation-with-password"):
    expected_amount = 1
    if self.normal_user is not None:
      # If user already exists we do not expect to send an email
      expected_amount = 0
    
    mail_message_list = [i for i in subscription_request.getFollowUpRelatedValueList(
      portal_type="Mail Message") if notification_message in i.getTitle()]

    self.assertEqual(len(mail_message_list), expected_amount)
    if not expected_amount:
      return

    mail_message = mail_message_list[0]
    self.assertEqual(
      "TestSubscriptionSkins Notification Message %s %s" % (
        subscription_request.getLanguage(), notification_message),
      mail_message.getTitle())
    self.assertIn(subscription_request.getDefaultEmailText(), \
                 mail_message.getTextContent())
    self.assertIn(subscription_request.getDestinationSectionTitle(), \
      mail_message.getTextContent())

  def checkEmailPaymentNotification(self, subscription_request,
                 notification_message="subscription_request-payment-is-ready"):
    mail_message_list = [i for i in subscription_request.getFollowUpRelatedValueList(
      portal_type="Mail Message") if notification_message in i.getTitle()]

    self.assertEqual(len(mail_message_list), 1)
    mail_message = mail_message_list[0]
    self.assertEqual(
      "TestSubscriptionSkins Notification Message %s %s" % (
         subscription_request.getLanguage(), notification_message),
      mail_message.getTitle())
    invoice = subscription_request.SubscriptionRequest_verifyPaymentBalanceIsReady()
    self.assertEqual(invoice.getSimulationState(), 'stopped')
    self.assertIn(invoice.getRelativeUrl(), \
                 mail_message.getTextContent())
    self.assertIn(subscription_request.getDestinationSectionTitle(), \
      mail_message.getTextContent())

  def checkEmailInstanceNotification(self, subscription_request,
                 notification_message="subscription_request-instance-is-ready"):
    mail_message_list = [i for i in subscription_request.getFollowUpRelatedValueList(
      portal_type="Mail Message") if notification_message in i.getTitle()]

    self.assertEqual(len(mail_message_list), 1)
    mail_message = mail_message_list[0]
    self.assertEqual(
      "TestSubscriptionSkins Notification Message %s %s" % (
        subscription_request.getLanguage(), notification_message),
      mail_message.getTitle())
    instance_tree = subscription_request.getAggregateValue()
    self.assertEqual(instance_tree.getSlapState(), 'start_requested')
    self.assertIn(instance_tree.getRelativeUrl(), \
                 mail_message.getTextContent())
    self.assertIn(subscription_request.getDestinationSectionTitle(), \
      mail_message.getTextContent())

  def checkRelatedInstance(self, subscription_request):
    instance = self._checkRelatedInstance(subscription_request)
    self.assertEqual(instance.getAggregate(), None)

  def _checkRelatedInstance(self, subscription_request):
    instance_tree = subscription_request.getAggregateValue()
    self.assertNotEqual(instance_tree, None)

    self.assertEqual(subscription_request.getUrlString(),
                     instance_tree.getUrlString())
    self.assertEqual(subscription_request.getRootSlave(),
                     instance_tree.getRootSlave())
    self.assertEqual(instance_tree.getTextContent(),
      '<?xml version="1.0" encoding="utf-8"?>\n<instance>\n</instance>')
    #self.assertEqual(trial_request.getSlaXml(), '<?xml version="1.0" encoding="utf-8"?>\n<instance>\n</instance>')
    self.assertEqual(instance_tree.getSourceReference(), "default")

    instance_list = instance_tree.getSpecialiseRelatedValueList(
              portal_type=["Software Instance", "Slave Instance"])
    self.assertEqual(1,len(instance_list))

    return instance_list[0]

  def checkAllocationOnRelatedInstance(self, subscription_request):
    instance = self._checkRelatedInstance(subscription_request)
    self.assertNotEqual(instance.getAggregate(), None)

  def checkAggregatedSalePackingList(self, subscription_request, sale_packing_list):

    self.assertEqual(len(sale_packing_list.objectValues()), 2)

    sale_packing_list_line = [ i for i in sale_packing_list.objectValues()
      if i.getResource() == "service_module/slapos_instance_subscription"][0]

    quantity = subscription_request.getQuantity()
    if subscription_request.getPriceCurrency() == "currency_module/CNY":
      expected_individual_price_without_tax = self.expected_zh_individual_price_without_tax
      expected_reservation_fee = self.expected_zh_reservation_fee_without_tax
    else:
      expected_individual_price_without_tax = self.expected_individual_price_without_tax
      expected_reservation_fee = self.expected_reservation_fee_without_tax
      
    # The values are without tax
    self.assertEqual(sale_packing_list_line.getQuantity(), 1*quantity)
    self.assertEqual(round(sale_packing_list_line.getPrice(), 2),
      round(expected_individual_price_without_tax, 2))
    self.assertEqual(round(sale_packing_list_line.getTotalPrice(), 2), 
      round(1*expected_individual_price_without_tax*quantity, 2))

    self.assertEqual(sale_packing_list.getCausality(),
                     subscription_request.getRelativeUrl())

    sale_packing_list_line = [ i for i in sale_packing_list.objectValues()
      if i.getResource() == "service_module/slapos_reservation_refund"][0]

    quantity = subscription_request.getQuantity()
    # The values are without tax
    self.assertEqual(sale_packing_list_line.getQuantity(), 1)
    self.assertEqual(round(sale_packing_list_line.getPrice(), 2),
                     -round(expected_reservation_fee*quantity, 2))
    self.assertEqual(round(sale_packing_list_line.getTotalPrice(), 2),
                   -round(expected_reservation_fee*quantity, 2))

    self.assertEqual(sale_packing_list.getCausality(),
                     subscription_request.getRelativeUrl())

    self.assertEqual(sale_packing_list.getPriceCurrency(),
                     subscription_request.getPriceCurrency())

  def makeCloudInvitationToken(self, max_invoice_delay=0, max_invoice_credit_eur=0.0,
                                    max_invoice_credit_cny=0.0):
    
    self.login()
    contract_invitation_token = self.portal.invitation_token_module.newContent(
      portal_type="Contract Invitation Token",
      maximum_invoice_delay=max_invoice_delay
    )

    if max_invoice_credit_eur > 0:
      contract_invitation_token.newContent(
      maximum_invoice_credit=max_invoice_credit_eur,
      price_currency="currency_module/EUR")

    if max_invoice_credit_cny > 0:
      contract_invitation_token.newContent(
      maximum_invoice_credit=max_invoice_credit_cny,
      price_currency="currency_module/CNY")

    contract_invitation_token.validate()
    self.logout()
    return contract_invitation_token

  @changeSkin('Hal')
  def _requestSubscription(self, **kw):
    if self.cloud_invitation_token is not None:
      kw["token"] = self.cloud_invitation_token.getId()
    if self.resource_variation_reference is not None:
      kw["variation_reference"] = self.resource_variation_reference
    return self.web_site.hateoas.SubscriptionRequestModule_requestSubscriptionProxy(**kw)

  @changeSkin('Hal')
  def _requestSubscriptionViaChineseWebsite(self, **kw):
    if self.cloud_invitation_token is not None:
      kw["token"] = self.cloud_invitation_token.getId()
    if 'target_language' not in kw:
      kw["target_language"] = "zh"
    if self.resource_variation_reference is not None:
      kw["variation_reference"] = self.resource_variation_reference
    kw["subscription_reference"] = self.subscription_condition.getReference().replace("_zh", "")

    original_mode = self.portal.portal_secure_payments.slapos_wechat_test.getWechatMode()
    self._simulatePaymentTransaction_getVADSUrlDict()
    try:
      self.portal.portal_secure_payments.slapos_wechat_test.setWechatMode("UNITTEST")
      self.logout()
      self.changeSkin('Hal')
      return self.web_site.hateoas.SubscriptionRequestModule_requestSubscriptionProxy(**kw)
    finally:
      self._dropPaymentTransaction_getVADSUrlDict()
      self.portal.portal_secure_payments.slapos_wechat_test.setWechatMode(original_mode)

  def getAggregatedSalePackingList(self, subscription_request, specialise):
    person = subscription_request.getDestinationSectionValue()
    person_uid = person.getUid()

    trade_condition = person.Person_getAggregatedSubscriptionSaleTradeConditionValue(specialise)
    specialise_uid = self.portal.restrictedTraverse(trade_condition).getUid()

    return self.portal.portal_catalog(
      portal_type='Sale Packing List',
      simulation_state='confirmed',
      causality_state='solved',
      causality_uid=subscription_request.getUid(),
      destination_decision_uid=person_uid,
      specialise_uid=specialise_uid)

  def getDivergedAggregatedSalePackingList(self, subscription_request, specialise):
    person_uid = subscription_request.getDestinationSectionValue().getUid()
    specialise_uid = self.portal.restrictedTraverse(specialise).getUid()

    return self.portal.portal_catalog(
      portal_type='Sale Packing List',
      simulation_state='confirmed',
      causality_state='diverged',
      causality_uid=subscription_request.getUid(),
      destination_decision_uid=person_uid,
      specialise_uid=specialise_uid)

  def getSubscriptionSalePackingList(self, subscription_request):
    person_uid = subscription_request.getDestinationSectionValue().getUid()
    specialise_uid = self.portal.restrictedTraverse(
      "sale_trade_condition_module/slapos_subscription_trade_condition").getUid()

    return self.portal.portal_catalog(
      portal_type='Sale Packing List',
      simulation_state='delivered',
      causality_state='solved',
      destination_decision_uid=person_uid,
      specialise_uid=specialise_uid)

  def createPublicServerForAdminUser(self):
    # hooray, now it is time to create compute_nodes
    self.login(self.admin_user.getUserId())

    # Create a Public Server for admin user, and allow
    subscription_server_title = 'Trial Public Server for Admin User %s' % self.new_id
    subscription_server_id = self.requestComputeNode(subscription_server_title)
    subscription_server = self.portal.portal_catalog.getResultValue(
        portal_type='Compute Node', reference=subscription_server_id)
    self.setAccessToMemcached(subscription_server)
    self.assertNotEqual(None, subscription_server)
    self.setServerOpenSubscription(subscription_server)

    # and install some software on them
    subscription_server_software = self.subscription_condition.getUrlString()
    self.supplySoftware(subscription_server, subscription_server_software)

    # format the compute_nodes
    self.formatComputeNode(subscription_server)

    # Without certificate computer isnt a user yet.
    subscription_server.generateCertificate()

    self.tic()
    self.logout()
    return subscription_server

  def requestAndCheckInstanceTree(self, amount, name, 
              default_email_text):
  
    self.logout()
    user_input_dict = {
      "name": name,
      "amount" : amount}
    self._requestSubscription(
      subscription_reference=self.subscription_condition.getReference(),
      user_input_dict=user_input_dict,
      email=default_email_text,
      confirmation_required=False)

    self.login()
    # I'm not sure if this is realistic
    self.tic()

    subscription_request = self.getSubscriptionRequest(
      default_email_text, self.subscription_condition)

    self.assertEqual(self.expected_price_currency,
      subscription_request.getPriceCurrency())

    self.assertEqual(self.subscription_condition.getSource(),
      subscription_request.getSource())
    
    self.assertEqual(self.subscription_condition.getSourceSection(),
      subscription_request.getSourceSection())
    
    self.assertEqual(self.expected_notification_language,
      subscription_request.getLanguage())

    self.checkDraftSubscriptionRequest(subscription_request,
                      default_email_text, self.subscription_condition,
                      amount=amount)

    # Check Payment and pay it.
    self.checkAndPaySubscriptionPayment([subscription_request])
    self.tic()

    # Call alarm to check payment and invoice and move foward to planned.
    self.stepCallSlaposSubscriptionRequestProcessDraftAlarm()
    self.tic()

    self.checkPlannedSubscriptionRequest(subscription_request,
               default_email_text, self.subscription_condition)

    # Call alarm to mark subscription request as ordered, bootstrap the user
    # and check if email is sent, once done move to ordered state.
    self.stepCallSlaposSubscriptionRequestProcessPlannedAlarm()
    self.tic()

    self.checkOrderedSubscriptionRequest(subscription_request,
               default_email_text, self.subscription_condition)

    # Call alarm to make the request of the instance?
    self.stepCallSlaposSubscriptionRequestProcessOrderedAlarm()
    self.tic()

    # The alarms might be called multiple times for move each step
    self.stepCallSlaposSubscriptionRequestProcessOrderedAlarm()
    self.tic()

    sale_packing_list_list = self.portal.portal_catalog(
      causality_uid = subscription_request.getUid(),
      title="Reservation Deduction",
      portal_type="Sale Packing List"
    )
    self.assertEqual(len(sale_packing_list_list), 1)
    sale_packing_list = sale_packing_list_list[0]

    self.assertEqual(sale_packing_list.getPriceCurrency(),
                     subscription_request.getPriceCurrency())
    self.assertEqual(sale_packing_list.getSpecialise(),
      "sale_trade_condition_module/slapos_reservation_refund_trade_condition")

    if subscription_request.getPriceCurrency() == "currency_module/CNY":
      self.assertEqual(round(sale_packing_list.getTotalPrice(), 2),
                     -round(self.expected_zh_reservation_fee_without_tax*amount, 2))

    else:
      self.assertEqual(round(sale_packing_list.getTotalPrice(), 2),
                     -round(self.expected_reservation_fee_without_tax*amount, 2))

    return subscription_request

  def _checkSubscriptionDeploymentAndSimulation(self, subscription_request_list,
                                                default_email_text, subscription_server):

    for subscription_request in subscription_request_list:
      # Check if instance was requested
      self.checkRelatedInstance(subscription_request)

    self.simulateSlapgridCP(subscription_server)
    self.tic()

    self.stepCallSlaposAllocateInstanceAlarm()
    self.tic()

    # now instantiate it on compute_node and set some nice connection dict
    self.simulateSlapgridCP(subscription_server)
    self.tic()

    for subscription_request in subscription_request_list:
      # Re-check, as instance shouldn't be allocated until
      # the confirmation of the new Payment.
      self.checkAllocationOnRelatedInstance(subscription_request)

    # generate simulation for open order
    self.stepCallUpdateOpenOrderSimulationAlarm()
    self.tic()

    # build subscription packing list
    self.stepCallSlaposTriggerBuildAlarm()
    self.tic()

    # stabilise build deliveries and expand them
    self.stepCallSlaposManageBuildingCalculatingDeliveryAlarm()
    self.tic()

    # build aggregated packing list
    self.stepCallSlaposTriggerAggregatedDeliveryOrderBuilderAlarm()
    self.tic()

    # stabilise aggregated deliveries and expand them
    self.stepCallSlaposManageBuildingCalculatingDeliveryAlarm()
    self.tic()

    # check if Packing list is generated with the right trade condition
    preference_tool = self.portal.portal_preferences
    aggregate_subscription_condition = \
      preference_tool.getPreferredAggregatedSubscriptionSaleTradeCondition()
    trade_condition = preference_tool.getPreferredAggregatedSaleTradeCondition()

    for subscription_request in subscription_request_list:
      instance_tree = subscription_request.getAggregateValue()
      self.assertEqual(instance_tree.getCausalityState(), "solved")

      sale_packing_list_list = self.getAggregatedSalePackingList(
        subscription_request, aggregate_subscription_condition)
      self.assertEqual(1, len(sale_packing_list_list))

      self.checkAggregatedSalePackingList(subscription_request, sale_packing_list_list[0])

      expected_sale_packing_list_amount = len(subscription_request_list) +\
        self.non_subscription_related_instance_amount

      self.assertEqual(expected_sale_packing_list_amount,
        len(self.getSubscriptionSalePackingList(subscription_request)))

      self.assertEqual(0, len(self.getAggregatedSalePackingList(
        subscription_request, trade_condition)))

    # Call this alarm shouldn't affect the delivery
    self.stepCallSlaposStartConfirmedAggregatedSalePackingListAlarm(
        accounting_date=DateTime('2222/01/01'))
    self.tic()

    for subscription_request in subscription_request_list:
      self.assertEqual(1, len(self.getAggregatedSalePackingList(
        subscription_request, aggregate_subscription_condition)))

    # Call this alarm shouldn't affect the delivery
    self.stepCallSlaposStartConfirmedAggregatedSubscriptionSalePackingListAlarm()
    self.tic()

    for subscription_request in subscription_request_list:
      self.assertEqual(0, len(self.getAggregatedSalePackingList(
        subscription_request, trade_condition)))

    # stabilise aggregated deliveries and expand them
    self.stepCallSlaposManageBuildingCalculatingDeliveryAlarm()
    self.tic()

    # deliver aggregated deliveries
    self.stepCallSlaposDeliverStartedAggregatedSalePackingListAlarm()
    self.tic()

    # stabilise aggregated deliveries and expand them
    self.stepCallSlaposManageBuildingCalculatingDeliveryAlarm()
    self.tic()

    # build aggregated invoices
    self.stepCallSlaposTriggerBuildAlarm()
    self.tic()

    # stabilise aggregated invoices and expand them
    self.stepCallSlaposManageBuildingCalculatingDeliveryAlarm()
    self.tic()

    # update invoices with their tax & discount
    self.stepCallSlaposTriggerBuildAlarm()
    self.tic()
    self.stepCallSlaposManageBuildingCalculatingDeliveryAlarm()
    self.tic()

    # update invoices with their tax & discount transaction lines
    self.stepCallSlaposTriggerBuildAlarm()
    self.tic()
    self.stepCallSlaposManageBuildingCalculatingDeliveryAlarm()
    self.tic()

    # stop the invoices and solve them again
    self.stepCallSlaposStopConfirmedAggregatedSaleInvoiceTransactionAlarm()
    self.tic()
    self.stepCallSlaposManageBuildingCalculatingDeliveryAlarm()
    self.tic()

    # trigger the CRM interaction
    self.stepCallSlaposCrmCreateRegularisationRequestAlarm()
    self.tic()

    # After the payment re-call the Alarm in order to confirm the subscription
    # Request.
    self.stepCallSlaposSubscriptionRequestProcessOrderedAlarm()
    self.tic()

    # The alarms might be called multiple times for move each step
    self.stepCallSlaposSubscriptionRequestProcessOrderedAlarm()
    self.tic()

    for subscription_request in subscription_request_list:
      # Instances should be allocated
      self.checkAllocationOnRelatedInstance(subscription_request)

    if not self.expected_free_reservation:
      # In a scenario where invitation token is used, we expect
      # that this script outputs True as user is below the maximum limit.
      expected_test_payment_balance = False
      expected_slap_state_after_subscription_is_confirmed = 'stop_requested'
    else:
      expected_test_payment_balance = True
      expected_slap_state_after_subscription_is_confirmed = 'start_requested'


    # Check if instance is on confirmed state
    for subscription_request in subscription_request_list:
      self.checkConfirmedSubscriptionRequest(subscription_request,
               default_email_text,
               subscription_request.getSpecialiseValue())

      self.assertEqual(expected_test_payment_balance,
          subscription_request.SubscriptionRequest_testPaymentBalance())
      
      self.assertEqual('start_requested',
        subscription_request.getAggregateValue().getSlapState())
      
    # The alarms might be called multiple times for move each step
    self.stepCallSlaposSubscriptionRequestProcessConfirmedAlarm()
    self.tic()

    for subscription_request in subscription_request_list:
      self.assertEqual(expected_test_payment_balance,
          subscription_request.SubscriptionRequest_testPaymentBalance())

      self.assertEqual(expected_slap_state_after_subscription_is_confirmed,
        subscription_request.getAggregateValue().getSlapState())

  def checkSubscriptionDeploymentAndSimulationWithReversalTransaction(self, default_email_text, subscription_server):
    
    subscription_request_list = self.getSubscriptionRequestList(
      default_email_text, self.subscription_condition)

    self._checkSubscriptionDeploymentAndSimulation(
      subscription_request_list, default_email_text, subscription_server)

    # Make payments and reinvoke alarm
    for subscription_request in subscription_request_list:
      self.createReversalInvoiceAndCancelPayment(subscription_request)
      self.tic()

    self.stepCallSlaposSubscriptionRequestProcessConfirmedAlarm()
    self.tic()

    for subscription_request in subscription_request_list:
      self.assertTrue(
        subscription_request.SubscriptionRequest_testPaymentBalance())
      
      self.assertEqual('start_requested',
        subscription_request.getAggregateValue().getSlapState())

    # On the second loop that email is send and state is moved to started
    self.stepCallSlaposSubscriptionRequestProcessConfirmedAlarm()
    self.tic()

    for subscription_request in subscription_request_list:
      self.assertTrue(
        subscription_request.SubscriptionRequest_testPaymentBalance())
      
      self.assertEqual('start_requested',
        subscription_request.getAggregateValue().getSlapState())

      self.checkStartedSubscriptionRequest(subscription_request,
               default_email_text, self.subscription_condition)
    
  def checkSubscriptionDeploymentAndSimulation(self, default_email_text, subscription_server):
    subscription_request_list = self.getSubscriptionRequestList(
      default_email_text, self.subscription_condition)

    self._checkSubscriptionDeploymentAndSimulation(
      subscription_request_list, default_email_text, subscription_server)

    if not self.expected_free_reservation:
      for subscription_request in subscription_request_list:
        if subscription_request.getPriceCurrency() == "currency_module/CNY":
          self.checkAndPayFirstMonthViaWechat(subscription_request)
        else:
          self.checkAndPayFirstMonth(subscription_request)
        self.tic()
    
    self.stepCallSlaposSubscriptionRequestProcessConfirmedAlarm()
    self.tic()

    for subscription_request in subscription_request_list:
      self.assertTrue(
        subscription_request.SubscriptionRequest_testPaymentBalance())
      
      self.assertEqual('start_requested',
        subscription_request.getAggregateValue().getSlapState())

    # On the second loop that email is send and state is moved to started
    self.stepCallSlaposSubscriptionRequestProcessConfirmedAlarm()
    self.tic()

    for subscription_request in subscription_request_list:
      self.assertTrue(
        subscription_request.SubscriptionRequest_testPaymentBalance())
      
      self.assertEqual('start_requested',
        subscription_request.getAggregateValue().getSlapState())

      self.checkStartedSubscriptionRequest(subscription_request,
               default_email_text, self.subscription_condition)

  def destroyAndCheckSubscription(self, default_email_text, subscription_server):

    if self.skip_destroy_and_check:
      return

    subscription_request_list = self.getSubscriptionRequestList(
      default_email_text, self.subscription_condition)

    for subscription_request in subscription_request_list:
      self.assertEqual('start_requested',
        subscription_request.getAggregateValue().getSlapState())

      # Destroy all instances and process 
      instance_tree = subscription_request.getAggregateValue()
      instance_tree.InstanceTree_requestPerson('destroyed')
      self.tic()

    self.stepCallSlaposSubscriptionRequestProcessStartedAlarm()
    self.tic()

    self.checkStoppedSubscriptionRequest(subscription_request,
               default_email_text, self.subscription_condition)

  def _test_subscription_scenario(self, amount=1):
    """ The admin creates an compute_node, user can request instances on it"""

    self.subscription_server = self.createPublicServerForAdminUser()

    # Call as anonymous... check response?
    default_email_text = "abc%s@nexedi.com" % self.new_id
    name="ABC %s" % self.new_id

    self.requestAndCheckInstanceTree(
      amount, name, default_email_text)

    self.checkSubscriptionDeploymentAndSimulation(
        default_email_text, self.subscription_server)

    self.destroyAndCheckSubscription(
      default_email_text, self.subscription_server
    )

    return default_email_text, name

  def _test_subscription_scenario_with_existing_user(self, amount=1, language=None):
    """ The admin creates an compute_node, user can request instances on it"""

    # Call as anonymous... check response?
    default_email_text = "abc%s@nexedi.com" % self.new_id
    name="ABC %s" % self.new_id

    self.login()
    self.createNormalUser(default_email_text, name, language)
    self.tic()

    self.subscription_server = self.createPublicServerForAdminUser()

    self.requestAndCheckInstanceTree(
      amount, name, default_email_text)

    self.checkSubscriptionDeploymentAndSimulation(
        default_email_text, self.subscription_server)

    subscription_request = self.getSubscriptionRequest(
      default_email_text, self.subscription_condition)

    self.assertEqual(self.normal_user,
                    subscription_request.getDestinationSectionValue())

    self.destroyAndCheckSubscription(
      default_email_text, self.subscription_server
    )

    return default_email_text, name

  def _test_subscription_scenario_with_existing_user_with_non_subscription_request(self, amount=1, language=None):
    # Call as anonymous... check response?
    default_email_text = "abc%s@nexedi.com" % self.new_id
    name="ABC %s" % self.new_id

    self.login()
    self.createNormalUser(default_email_text, name, language)
    self.tic()

    self.subscription_server = self.createPublicServerForAdminUser()

    # Disable on this test the pricing on the template to not generate debt before 
    # them expected
    line = self.portal.open_sale_order_module.\
      slapos_accounting_open_sale_order_line_template.\
      slapos_accounting_open_sale_order_line_template

    previous_price = line.getPrice()  
    line.setPrice(0.0)

    try:
      self.login(self.normal_user.getUserId())
      self.personRequestInstanceNotReady(
        software_release=self.subscription_condition.getUrlString(),
        software_type="default",
        partition_reference="_test_subscription_scenario_with_existing_user_extra_instance",
      )
  
      self.non_subscription_related_instance_amount = 1
      self.login()
      self.requestAndCheckInstanceTree(
        amount, name, default_email_text)
  
      self.checkSubscriptionDeploymentAndSimulation(
          default_email_text, self.subscription_server)
  
      subscription_request = self.getSubscriptionRequest(
        default_email_text, self.subscription_condition)
  
      self.assertEqual(self.normal_user,
                      subscription_request.getDestinationSectionValue())
  
      self.destroyAndCheckSubscription(
        default_email_text, self.subscription_server
      )
    finally:
      line.setPrice(previous_price)
    
    return default_email_text, name

  def _test_two_subscription_scenario(self, amount=1, create_invitation=False,
    max_invoice_delay=0, max_invoice_credit_eur=0.0, max_invoice_credit_cny=0.0):
    """ The admin creates an compute_node, user can request instances on it"""
 
    self.subscription_server = self.createPublicServerForAdminUser()

    # Call as anonymous... check response?
    default_email_text = "abc%s@nexedi.com" % self.new_id
    name="ABC %s" % self.new_id
    if create_invitation:
      self.login()
      self.cloud_invitation_token = self.makeCloudInvitationToken(
        max_invoice_delay=max_invoice_delay,
        max_invoice_credit_eur=max_invoice_credit_eur,
        max_invoice_credit_cny=max_invoice_credit_cny
      )

    self.logout()
    user_input_dict = {
      "name": name,
      "amount" : amount}
    self._requestSubscription(
      subscription_reference=self.subscription_condition.getReference(),
      user_input_dict=user_input_dict,
      email=default_email_text,
      confirmation_required=False)


    self.login()

    # I'm not sure if this is realistic
    self.tic()

    first_subscription_request = self.getSubscriptionRequest(
      default_email_text, self.subscription_condition)

    self.checkDraftSubscriptionRequest(first_subscription_request,
                      default_email_text, self.subscription_condition, amount=amount)

    # Check Payment and pay it.
    self.checkAndPaySubscriptionPayment([first_subscription_request])
    self.tic()

    # Call alarm to check payment and invoice and move foward to planned.
    self.stepCallSlaposSubscriptionRequestProcessDraftAlarm()
    self.tic()

    self.checkPlannedSubscriptionRequest(first_subscription_request,
               default_email_text, self.subscription_condition)

    # Call alarm to mark subscription request as ordered, bootstrap the user
    # and check if email is sent, once done move to ordered state.
    self.stepCallSlaposSubscriptionRequestProcessPlannedAlarm()
    self.tic()

    self.checkOrderedSubscriptionRequest(first_subscription_request,
               default_email_text, self.subscription_condition)

    if create_invitation:
      self.login()
      self.cloud_invitation_token = self.makeCloudInvitationToken(
        max_invoice_delay=max_invoice_delay,
        max_invoice_credit_eur=max_invoice_credit_eur,
        max_invoice_credit_cny=max_invoice_credit_cny
      )

    self.logout()
    # Request a second one, without require confirmation and verifing
    # the second subscription request
    user_input_dict = {
      "name": name,
      "amount" : amount}
    self._requestSubscription(
      subscription_reference=self.subscription_condition.getReference(),
      user_input_dict=user_input_dict,
      email=default_email_text,
      confirmation_required=False)

    self.login()
    self.tic()
    second_subscription_request = [ i for i in self.getSubscriptionRequestList(
      default_email_text, self.subscription_condition) if i.getSimulationState() == "draft"][0]

    self.checkDraftSubscriptionRequest(second_subscription_request,
                        default_email_text, self.subscription_condition)

    # Check Payment and pay it.
    self.checkAndPaySubscriptionPayment([second_subscription_request])
    self.tic()

    # Call alarm to check payment and invoice and move foward to planned.
    self.stepCallSlaposSubscriptionRequestProcessDraftAlarm()
    self.tic()

    self.checkPlannedSubscriptionRequest(second_subscription_request,
               default_email_text, self.subscription_condition)

    # Call alarm to mark subscription request as ordered, bootstrap the user
    # and check if email is sent, once done move to ordered state.
    self.stepCallSlaposSubscriptionRequestProcessPlannedAlarm()
    self.tic()

    self.checkOrderedSubscriptionRequest(second_subscription_request,
               default_email_text, self.subscription_condition,
               notification_message="subscription_request-confirmation-without-password")

    # Call alarm to make the request of the instance?
    self.stepCallSlaposSubscriptionRequestProcessOrderedAlarm()
    self.tic()

    # The alarms might be called multiple times for move each step
    self.stepCallSlaposSubscriptionRequestProcessOrderedAlarm()
    self.tic()

    self.checkSubscriptionDeploymentAndSimulation(
        default_email_text, self.subscription_server)

    self.destroyAndCheckSubscription(
      default_email_text, self.subscription_server
    )

    return default_email_text, name

  def _test_subscription_scenario_with_reversal_transaction(self, amount=1):
    """ The admin creates an compute_node, user can request instances on it"""

    self.subscription_server = self.createPublicServerForAdminUser()

    # Call as anonymous... check response?
    default_email_text = "abc%s@nexedi.com" % self.new_id
    name="ABC %s" % self.new_id
    self.requestAndCheckInstanceTree(amount, name, default_email_text)

    self.checkSubscriptionDeploymentAndSimulationWithReversalTransaction(
        default_email_text, self.subscription_server)

    self.destroyAndCheckSubscription(
      default_email_text, self.subscription_server
    )

    return default_email_text, name

  def _test_second_month_scenario(self, default_email_text):

    subscription_request_list = self.getSubscriptionRequestList(
      default_email_text, self.subscription_condition)

    # Ensure periodicity is correct
    for subscription_request in subscription_request_list:
      instance_tree = subscription_request.getAggregateValue()
      self.assertEqual(instance_tree.getPeriodicityMonthDay(),
        min(DateTime().day(), 28))

    self.pinDateTime(DateTime(DateTime().asdatetime() + datetime.timedelta(days=32)))
    self.addCleanup(self.unpinDateTime)

    self._checkSecondMonthSimulation(subscription_request_list,
          default_email_text, self.subscription_server)

    self.skip_destroy_and_check = 0

    self.destroyAndCheckSubscription(
      default_email_text, self.subscription_server
    )

class TestSlapOSSubscriptionScenario(TestSlapOSSubscriptionScenarioMixin):

  def test_subscription_scenario_with_single_vm(self):
    self._test_subscription_scenario(amount=1)

  def test_subscription_scenario_with_reversal_transaction(self):
    self._test_subscription_scenario_with_reversal_transaction(amount=1)

  def test_subscription_with_3_vms_scenario(self):
    self._test_subscription_scenario(amount=3)

  def test_two_subscription_scenario(self):
    self._test_two_subscription_scenario(amount=1)

  def test_subscription_scenario_with_existing_user(self):
    self._test_subscription_scenario_with_existing_user(amount=1, language="en")

  def test_subscription_scenario_with_existing_user_with_non_subscription_request(self):
    self._test_subscription_scenario_with_existing_user_with_non_subscription_request(amount=1, language="en")

  def test_subscription_scenario_with_existing_chinese_user(self):
    # Messages are in english, when subscribed via english website. Even if the chinese language is
    # defined at user level.
    self._test_subscription_scenario_with_existing_user(amount=1, language="zh")
