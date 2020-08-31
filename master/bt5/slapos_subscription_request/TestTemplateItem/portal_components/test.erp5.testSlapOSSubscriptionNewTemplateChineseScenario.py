# -*- coding:utf-8 -*-
##############################################################################
#
# Copyright (c) 2019 Nexedi SA and Contributors. All Rights Reserved.
#
# This program is free software: you can Use, Study, Modify and Redistribute
# it under the terms of the GNU General Public License version 3, or (at your
# option) any later version, as published by the Free Software Foundation.
#
# You can also Link and Combine this program with other software covered by
# the terms of any of the Free Software licenses or any of the Open Source
# Initiative approved licenses and Convey the resulting work. Corresponding
# source of such a combination shall include the source code for all other
# software used.
#
# This program is distributed WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See COPYING file for full licensing terms.
# See https://www.nexedi.com/licensing for rationale and options.
#
##############################################################################

from erp5.component.test.testSlapOSSubscriptionChineseScenario import TestSlapOSSubscriptionChineseScenarioMixin

class testSlapOSSubscriptionNewTemplateChineseScenario(TestSlapOSSubscriptionChineseScenarioMixin):

  def afterSetUp(self):
    TestSlapOSSubscriptionChineseScenarioMixin.afterSetUp(self)
    organisation = self.redefineAccountingTemplatesonPreferences()

    self.expected_source = organisation.getRelativeUrl()
    self.expected_source_section = organisation.getRelativeUrl()
    self.portal.portal_caches.clearAllCache()
    self.tic()

  def beforeTearDown(self):
    TestSlapOSSubscriptionChineseScenarioMixin.beforeTearDown(self)
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