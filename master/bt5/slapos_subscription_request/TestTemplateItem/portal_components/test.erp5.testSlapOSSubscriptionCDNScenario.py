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

class TestSlapOSSubscriptionCDNScenarioMixin(TestSlapOSSubscriptionScenarioMixin):

  def afterSetUp(self):
    TestSlapOSSubscriptionScenarioMixin.afterSetUp(self)
    self.expected_individual_price_without_tax = 5
    self.expected_individual_price_with_tax = 6.0
    self.expected_reservation_fee = 1.2
    self.expected_reservation_fee_without_tax = 1
    self.expected_reservation_quantity_tax = 1.0
    self.expected_reservation_tax = 0.2
    self.expected_price_currency = "currency_module/EUR"

    self.expected_zh_individual_price_without_tax = 40
    self.expected_zh_individual_price_with_tax = 40.4
    self.expected_zh_reservation_fee = 8.08
    self.expected_zh_reservation_fee_without_tax = 8.0
    self.expected_zh_reservation_quantity_tax = 8.0
    self.expected_zh_reservation_tax = 0.08

    self.resource_variation_reference = "CDN"
  
    self.login()
    # Overwrite default Subscription Condition.
    self.createSubscriptionCondition(slave=True)

    # some preparation
    self.logout()

  def createPublicServerForAdminUser(self):

    subscription_server = TestSlapOSSubscriptionScenarioMixin.createPublicServerForAdminUser(self)

    self.login()

    contract = self.admin_user.Person_generateCloudContract(batch=True)
    if contract.getValidationState() in ["draft", "invalidated"]:
      contract.validate()
      self.tic()


    # now instantiate it on compute_node and set some nice connection dict
    self.setServerOpenPersonal(subscription_server)

    self.login(self.admin_user.getUserId())
    self.personRequestInstanceNotReady(
      software_release=self.subscription_condition.getUrlString(),
      software_type=self.subscription_condition.getSourceReference(),
      partition_reference="InstanceForSlave%s" % self.new_id
    )

    self.stepCallSlaposAllocateInstanceAlarm()
    self.tic()

    self.personRequestInstance(
      software_release=self.subscription_condition.getUrlString(),
      software_type=self.subscription_condition.getSourceReference(),
      partition_reference="InstanceForSlave%s" % self.new_id
    )

    # now instantiate it on compute_node and set some nice connection dict
    self.simulateSlapgridCP(subscription_server)

    self.tic()
    self.login()
    self.setServerOpenSubscription(subscription_server)
    self.setAccessToMemcached(subscription_server)
    self.tic()
    self.simulateSlapgridCP(subscription_server)

    self.logout()
    return subscription_server

class TestSlapOSSubscriptionCDNScenario(TestSlapOSSubscriptionCDNScenarioMixin):

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

  def test_subscription_scenario_with_existing_chinese_user(self):
    # Messages are in chinese, when subscribed via chinese website. Even if the english language is
    # english
    self._test_subscription_scenario_with_existing_user(amount=1, language="zh")
