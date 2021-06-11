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

class testSlapOSSubscriptionDualOrganisationScenario(TestSlapOSSubscriptionScenarioMixin):

  def afterSetUp(self):
    TestSlapOSSubscriptionScenarioMixin.afterSetUp(self)
    fr_organisation, zh_organisation = self.redefineAccountingTemplatesonPreferencesWithDualOrganisation()

    self.expected_source = fr_organisation.getRelativeUrl()
    self.expected_source_section = fr_organisation.getRelativeUrl()
    self.expected_zh_reservation_fee = 189.88

    self.subscription_condition.edit(
      source=self.expected_source,
      source_section=self.expected_source_section
    )

    self.subscription_condition_zh = self.createChineseSubscriptionCondition()
    self.expected_zh_source = zh_organisation.getRelativeUrl()
    self.expected_zh_source_section = zh_organisation.getRelativeUrl()

    self.subscription_condition_zh.edit(
      source=self.expected_zh_source,
      source_section=self.expected_zh_source_section
    )

    self.portal.portal_caches.clearAllCache()
    self.tic()

  def beforeTearDown(self):
    TestSlapOSSubscriptionScenarioMixin.beforeTearDown(self)
    self.restoreAccountingTemplatesOnPreferences()
    self.portal.portal_caches.clearAllCache()
    self.tic()

  def requestAndCheckDualInstanceTree(self, amount, name, 
              default_email_text, language_list):
  
    self.logout()

    user_input_dict = {
      "name": name,
      "amount" : amount}
    request_kw = dict(
        subscription_reference=self.subscription_condition.getReference(),
        user_input_dict=user_input_dict,
        email=default_email_text,
        confirmation_required=False)

    all_subscription_requested_list = []
    for language in language_list:
      if language == "zh":
        self._requestSubscriptionViaChineseWebsite(**request_kw)
        subscription_condition = self.subscription_condition_zh
        expected_price_currency = "currency_module/CNY"
        expected_source_section =  self.expected_zh_source_section
      else:
        self._requestSubscription(**request_kw)
        subscription_condition = self.subscription_condition
        expected_price_currency = "currency_module/EUR"
        expected_source_section =  self.expected_source_section

      self.login()
      # I'm not sure if this is realistic
      self.tic()

      subscription_request_list = self.getSubscriptionRequestList(
        default_email_text, subscription_condition)
      for subscription_request in subscription_request_list:
        self.assertEqual(language,
                       subscription_request.getLanguage())

        self.assertEqual(expected_price_currency,
                         subscription_request.getPriceCurrency())

        self.assertEqual(expected_source_section,
                         subscription_request.getSourceSection())


        self.checkDraftSubscriptionRequest(subscription_request,
                      default_email_text,
                      subscription_request.getSpecialiseValue(),
                      amount=amount)
        self.tic()
        if subscription_request not in all_subscription_requested_list:
          all_subscription_requested_list.append(subscription_request)

    self.checkAndPaySubscriptionPayment(all_subscription_requested_list)
    self.tic()

    # Call alarm to check payment and invoice and move foward to planned.
    self.stepCallSlaposSubscriptionRequestProcessDraftAlarm()
    self.tic()

    for subscription_request in all_subscription_requested_list:
      self.checkPlannedSubscriptionRequest(subscription_request,
              default_email_text, 
              subscription_request.getSpecialiseValue())

    # Call alarm to mark subscription request as ordered, bootstrap the user
    # and check if email is sent, once done move to ordered state.
    self.stepCallSlaposSubscriptionRequestProcessPlannedAlarm()
    self.tic()

    for subscription_request in all_subscription_requested_list:
      self.checkOrderedSubscriptionRequest(subscription_request,
              default_email_text, 
              subscription_request.getSpecialiseValue())

    # Call alarm to make the request of the instance?
    self.stepCallSlaposSubscriptionRequestProcessOrderedAlarm()
    self.tic()

    # The alarms might be called multiple times for move each step
    self.stepCallSlaposSubscriptionRequestProcessOrderedAlarm()
    self.tic()

    for subscription_request in all_subscription_requested_list:
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
        expected_reservation_fee = self.expected_zh_reservation_fee_without_tax
      else:
        expected_reservation_fee = self.expected_reservation_fee_without_tax

      self.assertEqual(round(sale_packing_list.getTotalPrice(), 2),
                       -round(expected_reservation_fee*amount, 2))

    return all_subscription_requested_list


  def _test_subscription_scenario_with_dual_organisation(self, language_list, amount=1, language="en"):
    # Call as anonymous... check response?
    default_email_text = "abc%s@nexedi.com" % self.new_id
    name="ABC %s" % self.new_id

    self.login()
    self.createNormalUser(default_email_text, name, language)

    self.tic()

    self.subscription_server = self.createPublicServerForAdminUser()
    self.login()

    # Extra software from zh version
    subscription_server_software = self.subscription_condition_zh.getUrlString()
    self.supplySoftware(self.subscription_server, subscription_server_software)
    self.tic()
    self.logout()
    
    subscription_request_list = self.requestAndCheckDualInstanceTree(
      amount, name, default_email_text, language_list=language_list)

    self._checkSubscriptionDeploymentAndSimulation(
      subscription_request_list, default_email_text,
      self.subscription_server)

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
               default_email_text,
               subscription_request.getSpecialiseValue())

    for subscription_request in subscription_request_list:
      self.assertEqual(self.normal_user,
                    subscription_request.getDestinationSectionValue())

    if self.skip_destroy_and_check:
      return

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
               default_email_text,
               subscription_request.getSpecialiseValue())

    return default_email_text, name

  def test_subscription_scenario_with_dual_organisation_en(self):
    self._test_subscription_scenario_with_dual_organisation(["en", "zh", "en"], amount=1, language="en")

  def test_subscription_scenario_with_dual_organisation_zh(self):
    self._test_subscription_scenario_with_dual_organisation(["en", "zh", "zh"], amount=1, language="zh")

  def test_subscription_scenario_with_dual_organisation_en_2(self):
    self._test_subscription_scenario_with_dual_organisation(["en", "zh"], amount=2, language="en")

  def test_subscription_scenario_with_dual_organisation_zh_2(self):
    self._test_subscription_scenario_with_dual_organisation(["en", "zh"], amount=2, language="zh")

  def test_subscription_scenario_with_dual_organisation_en_only(self):
    self._test_subscription_scenario_with_dual_organisation(["en", "en", "en"], amount=1, language="en")

  def test_subscription_scenario_with_dual_organisation_zh_only(self):
    self._test_subscription_scenario_with_dual_organisation(["zh", "zh", "zh"], amount=1, language="zh")
