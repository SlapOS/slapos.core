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


from erp5.component.test.testSlapOSSubscriptionChineseScenario import TestSlapOSSubscriptionChineseScenarioMixin

class testSlapOSSubscriptionSecondMonthPaymentScenario(TestSlapOSSubscriptionChineseScenarioMixin):

  def test_subscription_scenario_with_single_vm(self):
    self.skip_destroy_and_check = 1
    default_email_text, _ = self._test_subscription_scenario(amount=1)
    self._test_second_month_scenario(default_email_text)

  def test_subscription_with_3_vms_scenario(self):
    self.skip_destroy_and_check = 1
    default_email_text, _ = self._test_subscription_scenario(amount=3)
    self._test_second_month_scenario(default_email_text)

  def test_subscription_scenario_with_reversal_transaction(self):
    self.skip_destroy_and_check = 1
    default_email_text, _ = self._test_subscription_scenario_with_reversal_transaction(amount=1)
    self._test_second_month_scenario(default_email_text)

  def test_two_subscription_scenario(self):
    self.skip_destroy_and_check = 1
    default_email_text, _ = self._test_two_subscription_scenario(amount=1)
    self._test_second_month_scenario(default_email_text)

  def test_subscription_scenario_with_existing_chienese_user(self):
    self.skip_destroy_and_check = 1
    default_email_text, _ = self._test_subscription_scenario_with_existing_user(amount=1, language="zh")
    self._test_second_month_scenario(default_email_text)

  def test_subscription_scenario_with_existing_english_user(self):
    self.skip_destroy_and_check = 1
    default_email_text, _ = self._test_subscription_scenario_with_existing_user(amount=1, language="en")
    self._test_second_month_scenario(default_email_text)
