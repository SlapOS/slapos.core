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

from erp5.component.test.testSlapOSSubscriptionCDNScenario import TestSlapOSSubscriptionCDNScenarioMixin
from erp5.component.test.SlapOSTestCaseMixin import changeSkin

class TestSlapOSSubscriptionChineseCDNScenarioMixin(TestSlapOSSubscriptionCDNScenarioMixin):

  def afterSetUp(self):
    self.expected_slapos_organisation = self.expected_zh_slapos_organisation
    TestSlapOSSubscriptionCDNScenarioMixin.afterSetUp(self)
    self.expected_price_currency = "currency_module/CNY"
    self.normal_user = None
    self.expected_notification_language = "zh"
    self.login()

  @changeSkin('Hal')
  def _requestSubscription(self, **kw):
    return self._requestSubscriptionViaChineseWebsite(**kw)

  def createSubscriptionCondition(self, slave=False):
    self.subscription_condition = self.createChineseSubscriptionCondition(
       slave=slave)

class TestSlapOSSubscriptionCDNChineseScenario(TestSlapOSSubscriptionChineseCDNScenarioMixin):

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

  def test_subscription_scenario_with_existing_user_with_non_subscription_request(self):
    self._test_subscription_scenario_with_existing_user_with_non_subscription_request(amount=1, language="en")

  def test_subscription_scenario_with_existing_english_user(self):
    # Messages are in chinese, when subscribed via chinese website. Even if the english language is
    # english
    self._test_subscription_scenario_with_existing_user(amount=1, language="en")