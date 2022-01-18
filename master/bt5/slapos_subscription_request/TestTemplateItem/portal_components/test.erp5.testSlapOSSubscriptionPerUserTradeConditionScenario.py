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


class testSlapOSSubscriptionPerUserTradeConditionScenario(TestSlapOSSubscriptionScenarioMixin):

  def createCustomUserSaleTradeCondition(self, person):

    root_trade_condition = self.portal.portal_preferences.\
      getPreferredAggregatedSubscriptionSaleTradeCondition()

    root_trade_condition_value = self.portal.restrictedTraverse(
      root_trade_condition)

    user_trade_condition = root_trade_condition_value.\
                                     Base_createCloneDocument(batch_mode=1)
    user_trade_condition.manage_delObjects([x for x in
                                            user_trade_condition.contentIds()])

    user_trade_condition.edit(
      title="TEST Trade Condition for %s" % person.getTitle(),
      reference="%s_custom_%s" % (user_trade_condition.getReference(), user_trade_condition.getUid()),
      destination_section_value=person,
      specialise_value=self.subscription_condition.getSpecialiseValue(),
      payment_mode='payzen',
      price_currency_value=self.subscription_condition.getSpecialiseValue().getPriceCurrency(),
    )

    user_trade_condition.validate()
    self.subscription_condition.edit(specialise_value=user_trade_condition)
    return user_trade_condition

  def _test_subscription_scenario_with_custom_condition(self, amount=1, language=None):
    """ The admin creates an compute_node, user can request instances on it"""

    # Call as anonymous... check response?
    default_email_text = "abc%s@nexedi.com" % self.new_id
    name="ABC %s" % self.new_id

    self.login()
    self.createNormalUser(default_email_text, name, language)
    self.createCustomUserSaleTradeCondition(self.normal_user)
    
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

  def test_custom_scenario(self):
    self._test_subscription_scenario_with_custom_condition(amount=1, language="en")

class testSlapOSSubscriptionPerUserTradeConditionScenarioDetaxed(TestSlapOSSubscriptionScenarioMixin):

  def afterSetUp(self):

    TestSlapOSSubscriptionScenarioMixin.afterSetUp(self)

    self.expected_individual_price_without_tax = 162.5
    self.expected_individual_price_with_tax = 195
    self.expected_reservation_fee = 25.00
    self.expected_reservation_fee_without_tax = 20.83
    self.expected_reservation_quantity_tax = 20.83
    self.expected_reservation_tax = 4.17

  def createDetaxedUserSaleTradeCondition(self, person):

    root_trade_condition = self.portal.portal_preferences.\
      getPreferredAggregatedSubscriptionSaleTradeCondition()
    
    root_trade_condition_value = self.portal.restrictedTraverse(
      root_trade_condition)

    user_trade_condition = root_trade_condition_value.\
                                     Base_createCloneDocument(batch_mode=1)

    user_trade_condition.edit(
      title="TEST Trade Condition for %s" % person.getTitle(),
      reference="%s_detaxed_%s" % (user_trade_condition.getReference(), user_trade_condition.getUid()),
      destination_section_value=person,
      specialise_value=self.subscription_condition.getSpecialiseValue(),
      payment_mode='payzen',
      price_currency_value=self.subscription_condition.getSpecialiseValue().getPriceCurrency(),
    )

    user_trade_condition.manage_delObjects([x for x in
                                            user_trade_condition.contentIds()])
    user_trade_condition.newContent(
      portal_type="Sale Supply Line",
      base_price=self.expected_reservation_fee_without_tax,
      resource='service_module/slapos_reservation_fee_2',
    )
    user_trade_condition.newContent(
      portal_type="Sale Supply Line",
      base_price=self.expected_individual_price_with_tax,
      resource='service_module/slapos_instance_subscription',
    )

    user_trade_condition.validate()
    self.subscription_condition.edit(specialise_value=user_trade_condition)
    return user_trade_condition

  def _test_subscription_scenario_with_detaxed_condition(self, amount=1, language=None):
    """ The admin creates an compute_node, user can request instances on it"""

    # Call as anonymous... check response?
    default_email_text = "abc%s@nexedi.com" % self.new_id
    name="ABC %s" % self.new_id

    self.login()
    self.createNormalUser(default_email_text, name, language)
    self.createDetaxedUserSaleTradeCondition(self.normal_user)
    
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

  def test_detaxed_scenario(self):
    self._test_subscription_scenario_with_detaxed_condition(amount=1, language="en")
