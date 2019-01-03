# Copyright (c) 2013 Nexedi SA and Contributors. All Rights Reserved.
from erp5.component.test.SlapOSTestCaseMixin import \
  SlapOSTestCaseMixin
from DateTime import DateTime

class TestSlapOSTrialRequestProcessDraft(SlapOSTestCaseMixin):

  def test_alarm_slapos_trial_process_draft_trial_request(self):
    script_name = "TrialRequest_processRequest"
    alarm = self.portal.portal_alarms.slapos_trial_process_draft_trial_request

    trial_request = self.portal.trial_request_module.newContent(
        portal_type='Trial Request',
        title="Test Trial Request %s" % self.new_id,
        reference="TESTTRIALREQUEST-%s" % self.new_id
    )

    self._test_alarm(
      alarm, trial_request, script_name)

  def test_alarm_slapos_trial_process_submitted_trial_request(self):
    script_name = "TrialRequest_processNotify"
    alarm = self.portal.portal_alarms.slapos_trial_process_submitted_trial_request

    trial_request = self.portal.trial_request_module.newContent(
        portal_type='Trial Request',
        title="Test Trial Request %s" % self.new_id,
        reference="TESTTRIALREQUEST-%s" % self.new_id
    )
    trial_request.submit()

    self._test_alarm(
      alarm, trial_request, script_name)

  def test_alarm_slapos_trial_process_validated_trial_request(self):
    script_name = "TrialRequest_processDestroy"
    alarm = self.portal.portal_alarms.slapos_trial_process_validated_trial_request

    trial_request = self.portal.trial_request_module.newContent(
        portal_type='Trial Request',
        title="Test Trial Request %s" % self.new_id,
        reference="TESTTRIALREQUEST-%s" % self.new_id
    )
    trial_request.submit()
    trial_request.validate()

    def getCreationDate(self):
      return DateTime() - 2

    from Products.ERP5Type.Base import Base

    original_get_creation = Base.getCreationDate
    Base.getCreationDate = getCreationDate

    try:
      self._test_alarm(
        alarm, trial_request, script_name)
    finally:
      Base.getCreationDate = original_get_creation

  def test_alarm_slapos_trial_process_validated_trial_request_too_soon(self):
    script_name = "TrialRequest_processDestroy"
    alarm = self.portal.portal_alarms.slapos_trial_process_validated_trial_request

    trial_request = self.portal.trial_request_module.newContent(
        portal_type='Trial Request',
        title="Test Trial Request %s" % self.new_id,
        reference="TESTTRIALREQUEST-%s" % self.new_id
    )
    trial_request.submit()
    trial_request.validate()

    self._test_alarm_not_visited(
        alarm, trial_request, script_name)
