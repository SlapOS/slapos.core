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

class testSlapOSSubscriptionNewTemplateScenario(TestSlapOSSubscriptionScenarioMixin):

  def afterSetUp(self):
    TestSlapOSSubscriptionScenarioMixin.afterSetUp(self)
    organisation = self.redefineAccountingTemplatesonPreferences()

    self.expected_source = organisation.getRelativeUrl()
    self.expected_source_section = organisation.getRelativeUrl()

    # Set those values (source and source section) are only meaninfull if 
    # the templates on preferences differ from Chinese and European organisations.
    self.subscription_condition.edit(
      source=None,
      source_section=None
    )

    self.portal.portal_caches.clearAllCache()
    self.tic()

  def beforeTearDown(self):
    TestSlapOSSubscriptionScenarioMixin.beforeTearDown(self)
    self.restoreAccountingTemplatesOnPreferences()
    self.portal.portal_caches.clearAllCache()
    self.tic()

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
