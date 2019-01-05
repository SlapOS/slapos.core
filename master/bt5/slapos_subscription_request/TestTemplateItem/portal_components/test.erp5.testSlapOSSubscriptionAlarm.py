# Copyright (c) 2013 Nexedi SA and Contributors. All Rights Reserved.
from erp5.component.test.SlapOSTestCaseMixin import \
  SlapOSTestCaseMixin

class TestSlapOSSubscriptionRequestProcessDraft(SlapOSTestCaseMixin):

  def test_alarm_slapos_subscription_request_process_draft(self):
    script_name = "SubscriptionRequest_verifyPaymentTransaction"
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
    subscription_request.planned()

    self._test_alarm(
      alarm, subscription_request, script_name)

  def test_alarm_slapos_subscription_request_process_ordered(self):
    script_name = "SubscriptionRequest_checkPaymentBalance"
    alarm = self.portal.portal_alarms.slapos_subscription_request_process_ordered

    subscription_request = self.portal.subscription_request_module.newContent(
        portal_type='Subscription Request',
        title="Test Subscription Request %s" % self.new_id,
        reference="TESTSUBSCRIPTIONREQUEST-%s" % self.new_id
    )
    subscription_request.planned()
    subscription_request.ordered()

    self._test_alarm(
      alarm, subscription_request, script_name)
