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
#from erp5.component.test.SlapOSTestCaseMixin import changeSkin


class TestSlapOSSubscriptionCancellationScenario(TestSlapOSSubscriptionScenarioMixin):

  def invokeBasicSimulationAlarmList(self):
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

  def test_subscription_scenario_reservation_cancellation_scenario(self):

    self.subscription_server = self.createPublicServerForAdminUser()

    # Call as anonymous... check response?
    default_email_text = "abc%s@nexedi.com" % self.new_id
    name="ABC %s" % self.new_id
    amount = 1

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

    self.checkDraftSubscriptionRequest(subscription_request,
                      default_email_text, self.subscription_condition, amount=amount)

    ### Here all fine, Now let's consider the user never payed. 
    invoice = subscription_request.getCausalityValue(
      portal_type="Sale Invoice Transaction")
    self.assertEqual(invoice.getSimulationState(), "confirmed")
    self.assertEqual(invoice.getCausalityState(), "building")
    # Invoices are not payed!
    payment_list = invoice.getCausalityRelatedValueList(portal_type="Payment Transaction")
    self.assertEqual(len(payment_list), 1)
    payment = payment_list[0]

    self.assertEqual(payment.getSimulationState(), "started")
    self.assertEqual(subscription_request.getSimulationState(), "draft")

    self.invokeBasicSimulationAlarmList()

    payment.cancel()
    self.invokeBasicSimulationAlarmList()

    # Call alarm to check payment and invoice and move foward to planned.
    self.stepCallSlaposSubscriptionRequestProcessDraftAlarm()
    self.tic()

    payment_list = invoice.getCausalityRelatedValueList(portal_type="Payment Transaction")
    self.assertEqual(len(payment_list), 1)
    payment = payment_list[0]
    self.assertEqual(payment.getSimulationState(), "cancelled")

    # Alarm is conflicting
    self.assertEqual(subscription_request.getSimulationState(), "cancelled")

  def test_subscription_scenario_reservation_cancellation_late_alarm_scenario(self):

    self.subscription_server = self.createPublicServerForAdminUser()

    # Call as anonymous... check response?
    default_email_text = "abc%s@nexedi.com" % self.new_id
    name="ABC %s" % self.new_id
    amount = 1

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

    self.checkDraftSubscriptionRequest(subscription_request,
                      default_email_text, self.subscription_condition, amount=amount)

    ### Here all fine, Now let's consider the user never payed. 
    invoice = subscription_request.getCausalityValue(
      portal_type="Sale Invoice Transaction")
    self.assertEqual(invoice.getSimulationState(), "confirmed")
    self.assertEqual(invoice.getCausalityState(), "building")
    # Invoices are not payed!
    payment_list = invoice.getCausalityRelatedValueList(portal_type="Payment Transaction")
    self.assertEqual(len(payment_list), 1)
    payment = payment_list[0]

    self.assertEqual(payment.getSimulationState(), "started")
    self.assertEqual(subscription_request.getSimulationState(), "draft")

    self.invokeBasicSimulationAlarmList()

    # stop the invoices and solve them again
    self.stepCallSlaposStopConfirmedAggregatedSaleInvoiceTransactionAlarm()
    self.tic()
    self.stepCallSlaposManageBuildingCalculatingDeliveryAlarm()
    self.tic()
    self.invokeBasicSimulationAlarmList()
    self.assertEqual(invoice.getSimulationState(), "stopped")
    self.assertEqual(invoice.getCausalityState(), "solved")

    self.assertEqual(payment.getSimulationState(), "started")

    # Cancel Payment and ensure all is cancelled along
    payment.cancel()
    self.assertEqual(payment.getSimulationState(), "cancelled")

    self.tic()
    self.assertEqual(invoice.getSimulationState(), "stopped")
    self.assertEqual(invoice.getCausalityState(), "solved")

    self.invokeBasicSimulationAlarmList()

    # Call alarm to check payment and invoice and move foward to planned.
    self.stepCallSlaposSubscriptionRequestProcessDraftAlarm()
    self.tic()

    payment_list = invoice.getCausalityRelatedValueList(portal_type="Payment Transaction")
    self.assertEqual(len(payment_list), 1)
    payment = payment_list[0]
    self.assertEqual(payment.getSimulationState(), "cancelled")
    self.assertEqual(invoice.getSimulationState(), "cancelled")

    # Alarm is conflicting
    self.assertEqual(subscription_request.getSimulationState(), "cancelled")


