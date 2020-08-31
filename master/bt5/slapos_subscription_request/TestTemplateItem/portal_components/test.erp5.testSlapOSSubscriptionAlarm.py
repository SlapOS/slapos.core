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
from erp5.component.test.SlapOSTestCaseMixin import \
  SlapOSTestCaseMixin

class TestSlapOSSubscriptionRequestProcessAlarm(SlapOSTestCaseMixin):

  def test_alarm_slapos_subscription_request_process_draft(self):
    script_name = "SubscriptionRequest_verifyReservationPaymentTransaction"
    alarm = self.portal.portal_alarms.slapos_subscription_request_process_draft

    subscription_request = self.portal.subscription_request_module.newContent(
        portal_type='Subscription Request',
        title="Test Subscription Request %s" % self.new_id,
        reference="TESTSUBSCRIPTIONREQUEST-%s" % self.new_id
    )

    self._test_alarm(
      alarm, subscription_request, script_name)

  def test_alarm_slapos_subscription_request_process_planned(self):
    script_name = "SubscriptionRequest_boostrapUserAccount"
    alarm = self.portal.portal_alarms.slapos_subscription_request_process_planned

    subscription_request = self.portal.subscription_request_module.newContent(
        portal_type='Subscription Request',
        title="Test Subscription Request %s" % self.new_id,
        reference="TESTSUBSCRIPTIONREQUEST-%s" % self.new_id
    )
    subscription_request.plan()

    self._test_alarm(
      alarm, subscription_request, script_name)

  def test_alarm_slapos_subscription_request_process_ordered(self):
    script_name = "SubscriptionRequest_processOrdered"
    alarm = self.portal.portal_alarms.slapos_subscription_request_process_ordered

    subscription_request = self.portal.subscription_request_module.newContent(
        portal_type='Subscription Request',
        title="Test Subscription Request %s" % self.new_id,
        reference="TESTSUBSCRIPTIONREQUEST-%s" % self.new_id
    )
    subscription_request.plan()
    subscription_request.order()

    self._test_alarm(
      alarm, subscription_request, script_name)

  def test_alarm_slapos_subscription_request_process_confirmed(self):
    script_name = "SubscriptionRequest_processConfirmed"
    alarm = self.portal.portal_alarms.slapos_subscription_request_process_confirmed

    subscription_request = self.portal.subscription_request_module.newContent(
        portal_type='Subscription Request',
        title="Test Subscription Request %s" % self.new_id,
        reference="TESTSUBSCRIPTIONREQUEST-%s" % self.new_id
    )
    subscription_request.plan()
    subscription_request.order()
    subscription_request.confirm()

    self._test_alarm(
      alarm, subscription_request, script_name)

  def test_alarm_slapos_subscription_request_process_started(self):
    script_name = "SubscriptionRequest_processStarted"
    alarm = self.portal.portal_alarms.slapos_subscription_request_process_started

    subscription_request = self.portal.subscription_request_module.newContent(
        portal_type='Subscription Request',
        title="Test Subscription Request %s" % self.new_id,
        reference="TESTSUBSCRIPTIONREQUEST-%s" % self.new_id
    )
    subscription_request.plan()
    subscription_request.order()
    subscription_request.confirm()
    subscription_request.start()
    
    self._test_alarm(
      alarm, subscription_request, script_name)
