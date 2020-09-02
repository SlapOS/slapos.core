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

class testSlapOSSubscriptionCloudInvitationTokenScenario(TestSlapOSSubscriptionChineseScenarioMixin):

  def test_subscription_scenario_with_single_vm_and_empty_invitation(self):
    self.cloud_invitation_token = self.makeCloudInvitationToken()
    self._test_subscription_scenario(amount=1)

  def test_subscription_with_3_vms_scenario_and_empty_invitation(self):
    self.cloud_invitation_token = self.makeCloudInvitationToken()
    self._test_subscription_scenario(amount=3)

  def test_subscription_scenario_with_reversal_transaction_and_empty_invitation(self):
    self.cloud_invitation_token = self.makeCloudInvitationToken()
    self._test_subscription_scenario_with_reversal_transaction(amount=1)

  def test_two_subscription_scenario_and_empty_invitation(self):
    self._test_two_subscription_scenario(amount=1)

  def test_subscription_scenario_with_existing_user_and_empty_invitation(self):
    self.cloud_invitation_token = self.makeCloudInvitationToken()
    self._test_subscription_scenario_with_existing_user(amount=1, language="zh")

  def test_subscription_scenario_with_existing_english_user_and_empty_invitation(self):
    self.cloud_invitation_token = self.makeCloudInvitationToken()
    self._test_subscription_scenario_with_existing_user(amount=1, language="en")

  def _init_test_with_valid_invitation(self):
    self.expected_reservation_fee = 0.0
    self.expected_reservation_quantity_tax = 0.0
    self.expected_reservation_tax = 0.0
    self.expected_free_reservation = 1

    self.cloud_invitation_token = self.makeCloudInvitationToken(
      max_invoice_delay=99,
      max_invoice_credit_eur=900,
      max_invoice_credit_cny=90000)

  def test_subscription_scenario_with_single_vm_with_invitation(self):
    self._init_test_with_valid_invitation()
    self._test_subscription_scenario(amount=1)

  def test_subscription_with_3_vms_scenario_with_invitation(self):
    self._init_test_with_valid_invitation()
    self._test_subscription_scenario(amount=3)

  def test_subscription_scenario_with_reversal_transaction_with_invitation(self):
    self._init_test_with_valid_invitation()
    self._test_subscription_scenario_with_reversal_transaction(amount=1)

  def test_two_subscription_scenario_with_invitation(self):
    self.expected_reservation_fee = 0.0
    self.expected_reservation_quantity_tax = 0.0
    self.expected_reservation_tax = 0.0
    self.expected_free_reservation = 1
    self._test_two_subscription_scenario(amount=1,
      create_invitation=True,
      max_invoice_delay=99,
      max_invoice_credit_eur=900,
      max_invoice_credit_cny=90000
    )

  def test_subscription_scenario_with_existing_user_with_invitation(self):
    self._init_test_with_valid_invitation()
    self._test_subscription_scenario_with_existing_user(amount=1, language="zh")

  def test_subscription_scenario_with_existing_english_user_with_invitation(self):
    self._init_test_with_valid_invitation()
    self._test_subscription_scenario_with_existing_user(amount=1, language="en")


