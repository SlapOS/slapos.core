# Copyright (c) 2013 Nexedi SA and Contributors. All Rights Reserved.
from erp5.component.test.SlapOSTestCaseMixin import \
  SlapOSTestCaseMixin, SlapOSTestCaseMixinWithAbort
from unittest import skip
from DateTime import DateTime

class TestSlapOSCRMCreateRegularisationRequest(SlapOSTestCaseMixin):

  def test_alarm_expected_person(self):
    new_id = self.generateNewId()
    person = self.portal.person_module.newContent(
      portal_type='Person',
      title="Test person %s" % new_id,
      reference="TESTPERS_%s" % new_id,
      default_email_text="%s@example.org" % new_id,
      )
    person.validate()

    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_create_regularisation_request
    self._test_alarm(alarm, person, "Person_checkToCreateRegularisationRequest")

  def test_alarm_no_email(self):
    new_id = self.generateNewId()
    person = self.portal.person_module.newContent(
      portal_type='Person',
      title="Test person %s" % new_id,
      reference="TESTPERS_%s" % new_id,
      )
    person.validate()

    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_create_regularisation_request
    self._test_alarm_not_visited(alarm, person, "Person_checkToCreateRegularisationRequest")

  def test_alarm_not_validated(self):
    new_id = self.generateNewId()
    person = self.portal.person_module.newContent(
      portal_type='Person',
      title="Test person %s" % new_id,
      reference="TESTPERS_%s" % new_id,
      default_email_text="%s@example.org" % new_id,
      )
    person.validate()
    person.invalidate()

    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_create_regularisation_request
    self._test_alarm_not_visited(alarm, person, "Person_checkToCreateRegularisationRequest")


class TestSlapOSCrmInvalidateSuspendedRegularisationRequest(SlapOSTestCaseMixinWithAbort):

  def createRegularisationRequest(self):
    new_id = self.generateNewId()
    return self.portal.regularisation_request_module.newContent(
      portal_type='Regularisation Request',
      title="Test Reg. Req.%s" % new_id,
      reference="TESTREGREQ-%s" % new_id,
      )

  def test_alarm_not_suspended_regularisation_request(self):
    ticket = self.createRegularisationRequest()
    ticket.validate()
    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_invalidate_suspended_regularisation_request
    self._test_alarm_not_visited(alarm, ticket, "RegularisationRequest_invalidateIfPersonBalanceIsOk")

  def test_alarm_suspended_regularisation_request(self):
    ticket = self.createRegularisationRequest()
    ticket.validate()
    ticket.suspend()
    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_invalidate_suspended_regularisation_request
    self._test_alarm(alarm, ticket, "RegularisationRequest_invalidateIfPersonBalanceIsOk")


class TestSlapOSCrmCancelInvoiceRelatedToSuspendedRegularisationRequest(SlapOSTestCaseMixinWithAbort):

  def createRegularisationRequest(self):
    new_id = self.generateNewId()
    return self.portal.regularisation_request_module.newContent(
      portal_type='Regularisation Request',
      title="Test Reg. Req.%s" % new_id,
      reference="TESTREGREQ-%s" % new_id,
      )

  def test_alarm_not_suspended_regularisation_request(self):
    ticket = self.createRegularisationRequest()
    ticket.validate()

    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_cancel_invoice
    self._test_alarm_not_visited(alarm, ticket,
      "RegularisationRequest_cancelInvoiceIfPersonOpenOrderIsEmpty")

  def test_alarm_suspended_regularisation_request(self):
    ticket = self.createRegularisationRequest()
    ticket.validate()
    ticket.suspend()

    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_cancel_invoice
    self._test_alarm(alarm, ticket,
      "RegularisationRequest_cancelInvoiceIfPersonOpenOrderIsEmpty")

class TestSlapOSCrmTriggerEscalationOnAcknowledgmentRegularisationRequest(SlapOSTestCaseMixinWithAbort):

  def createRegularisationRequest(self):
    new_id = self.generateNewId()
    return self.portal.regularisation_request_module.newContent(
      portal_type='Regularisation Request',
      title="Test Reg. Req.%s" % new_id,
      reference="TESTREGREQ-%s" % new_id,
      )

  def test_alarm_matching_regularisation_request(self):
    ticket = self.createRegularisationRequest()
    ticket.edit(resource='service_module/slapos_crm_acknowledgement')
    ticket.validate()
    ticket.suspend()

    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_trigger_acknowledgment_escalation
    self._test_alarm(alarm, ticket,
      "RegularisationRequest_triggerAcknowledgmentEscalation")

  def test_alarm_not_suspended(self):
    ticket = self.createRegularisationRequest()
    ticket.edit(resource='service_module/slapos_crm_acknowledgement')
    ticket.validate()

    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_trigger_acknowledgment_escalation
    self._test_alarm_not_visited(alarm, ticket,
      "RegularisationRequest_triggerAcknowledgmentEscalation")


  def test_alarm_not_expected_resource(self):
    ticket = self.createRegularisationRequest()
    ticket.validate()
    ticket.suspend()

    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_trigger_acknowledgment_escalation
    self._test_alarm_not_visited(alarm, ticket,
      "RegularisationRequest_triggerAcknowledgmentEscalation")

class TestSlapOSCrmTriggerEscalationOnStopReminderRegularisationRequest(SlapOSTestCaseMixinWithAbort):

  def createRegularisationRequest(self):
    new_id = self.generateNewId()
    return self.portal.regularisation_request_module.newContent(
      portal_type='Regularisation Request',
      title="Test Reg. Req.%s" % new_id,
      reference="TESTREGREQ-%s" % new_id,
      )

  def test_alarm_matching_regularisation_request(self):
    ticket = self.createRegularisationRequest()
    ticket.edit(resource='service_module/slapos_crm_stop_reminder')
    ticket.validate()
    ticket.suspend()

    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_trigger_stop_reminder_escalation
    self._test_alarm(alarm, ticket,
      "RegularisationRequest_triggerStopReminderEscalation")

  def test_alarm_not_suspended(self):
    ticket = self.createRegularisationRequest()
    ticket.edit(resource='service_module/slapos_crm_stop_reminder')
    ticket.validate()

    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_trigger_stop_reminder_escalation
    self._test_alarm_not_visited(alarm, ticket,
      "RegularisationRequest_triggerStopReminderEscalation")

  def test_alarm_not_expected_resource(self):
    ticket = self.createRegularisationRequest()
    ticket.validate()
    ticket.suspend()

    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_trigger_stop_reminder_escalation
    self._test_alarm_not_visited(alarm, ticket,
      "RegularisationRequest_triggerStopReminderEscalation")

class TestSlapOSCrmTriggerEscalationOnStopAcknowledgmentRegularisationRequest(SlapOSTestCaseMixinWithAbort):

  def createRegularisationRequest(self):
    new_id = self.generateNewId()
    return self.portal.regularisation_request_module.newContent(
      portal_type='Regularisation Request',
      title="Test Reg. Req.%s" % new_id,
      reference="TESTREGREQ-%s" % new_id,
      )

  def test_alarm_matching_regularisation_request(self):
    ticket = self.createRegularisationRequest()
    ticket.edit(resource='service_module/slapos_crm_stop_acknowledgement')
    ticket.validate()
    ticket.suspend()

    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_trigger_stop_acknowledgment_escalation
    self._test_alarm(alarm, ticket,
      "RegularisationRequest_triggerStopAcknowledgmentEscalation")

  def test_alarm_not_suspended(self):
    ticket = self.createRegularisationRequest()
    ticket.edit(resource='service_module/slapos_crm_stop_acknowledgement')
    ticket.validate()

    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_trigger_stop_acknowledgment_escalation
    self._test_alarm_not_visited(alarm, ticket,
      "RegularisationRequest_triggerStopAcknowledgmentEscalation")

  def test_alarm_not_expected_resource(self):
    ticket = self.createRegularisationRequest()
    ticket.validate()
    ticket.suspend()

    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_trigger_stop_acknowledgment_escalation
    self._test_alarm_not_visited(alarm, ticket,
      "RegularisationRequest_triggerStopAcknowledgmentEscalation")

class TestSlapOSCrmTriggerEscalationOnDeleteReminderRegularisationRequest(SlapOSTestCaseMixinWithAbort):

  def createRegularisationRequest(self):
    new_id = self.generateNewId()
    return self.portal.regularisation_request_module.newContent(
      portal_type='Regularisation Request',
      title="Test Reg. Req.%s" % new_id,
      reference="TESTREGREQ-%s" % new_id,
      )

  def test_alarm_matching_regularisation_request(self):
    ticket = self.createRegularisationRequest()
    ticket.edit(resource='service_module/slapos_crm_delete_reminder')
    ticket.validate()
    ticket.suspend()

    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_trigger_delete_reminder_escalation
    self._test_alarm(alarm, ticket, "RegularisationRequest_triggerDeleteReminderEscalation")

  def test_alarm_not_suspended(self):
    ticket = self.createRegularisationRequest()
    ticket.edit(resource='service_module/slapos_crm_delete_reminder')
    ticket.validate()

    self.tic()    
    alarm = self.portal.portal_alarms.\
          slapos_crm_trigger_delete_reminder_escalation
    self._test_alarm_not_visited(alarm, ticket, "RegularisationRequest_triggerDeleteReminderEscalation")


  def test_alarm_not_expected_resource(self):
    ticket = self.createRegularisationRequest()
    ticket.validate()
    ticket.suspend()

    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_trigger_delete_reminder_escalation
    self._test_alarm_not_visited(alarm, ticket, "RegularisationRequest_triggerDeleteReminderEscalation")

class TestSlapOSCrmStopHostingSubscription(SlapOSTestCaseMixinWithAbort):

  def createRegularisationRequest(self):
    new_id = self.generateNewId()
    return self.portal.regularisation_request_module.newContent(
      portal_type='Regularisation Request',
      title="Test Reg. Req.%s" % new_id,
      reference="TESTREGREQ-%s" % new_id,
      )

  def test_alarm_matching_regularisation_request(self):
    ticket = self.createRegularisationRequest()
    ticket.edit(resource='service_module/slapos_crm_delete_reminder')
    ticket.validate()
    ticket.suspend()

    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_stop_hosting_subscription
    self._test_alarm(alarm, ticket, "RegularisationRequest_stopHostingSubscriptionList")

  def test_alarm_matching_regularisation_request_2(self):
    ticket = self.createRegularisationRequest()
    ticket.edit(resource='service_module/slapos_crm_stop_acknowledgement')
    ticket.validate()
    ticket.suspend()

    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_stop_hosting_subscription
    self._test_alarm(alarm, ticket, "RegularisationRequest_stopHostingSubscriptionList")

  def test_alarm_not_suspended(self):
    ticket = self.createRegularisationRequest()
    ticket.edit(resource='service_module/slapos_crm_stop_acknowledgement')
    ticket.validate()

    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_stop_hosting_subscription
    self._test_alarm_not_visited(alarm, ticket, "RegularisationRequest_stopHostingSubscriptionList")


  def test_alarm_other_resource(self):
    ticket = self.createRegularisationRequest()
    ticket.edit(resource='service_module/slapos_acknowledgement')
    ticket.validate()
    ticket.suspend()

    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_stop_hosting_subscription
    self._test_alarm_not_visited(alarm, ticket, "RegularisationRequest_stopHostingSubscriptionList")


class TestSlapOSCrmDeleteHostingSubscription(SlapOSTestCaseMixinWithAbort):

  def createRegularisationRequest(self):
    new_id = self.generateNewId()
    return self.portal.regularisation_request_module.newContent(
      portal_type='Regularisation Request',
      title="Test Reg. Req.%s" % new_id,
      reference="TESTREGREQ-%s" % new_id,
      )

  def test_alarm_matching_regularisation_request(self):
    ticket = self.createRegularisationRequest()
    ticket.edit(resource='service_module/slapos_crm_delete_acknowledgement')
    ticket.validate()
    ticket.suspend()

    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_delete_hosting_subscription
    self._test_alarm(alarm, ticket, "RegularisationRequest_deleteHostingSubscriptionList")

  def test_alarm_not_suspended(self):
    ticket = self.createRegularisationRequest()
    ticket.edit(resource='service_module/slapos_crm_delete_acknowledgement')
    ticket.validate()

    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_delete_hosting_subscription
    self._test_alarm_not_visited(alarm, ticket, "RegularisationRequest_deleteHostingSubscriptionList")


  def test_alarm_other_resource(self):
    ticket = self.createRegularisationRequest()
    ticket.edit(resource='service_module/slapos_crm_delete_reminder')
    ticket.validate()
    ticket.suspend()

    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_delete_hosting_subscription
    self._test_alarm_not_visited(alarm, ticket, "RegularisationRequest_deleteHostingSubscriptionList")


class TestSlapOSCrmMonitoringCheckComputerState(SlapOSTestCaseMixinWithAbort):

  def test_alarm_check_public_computer_state(self):
    self._makeComputer()
    self.computer.edit(allocation_scope='open/public')
    self.tic()
    self.assertEqual(self.computer.getMonitorScope(), "enabled")
    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_check_computer_state
    self._test_alarm(alarm, self.computer, "Computer_checkState")

  def test_alarm_check_friend_computer_state(self):
    self._makeComputer()
    self.computer.edit(allocation_scope='open/friend')
    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_check_computer_state
    self._test_alarm(alarm, self.computer, "Computer_checkState")

  def test_alarm_check_personal_computer_state(self):
    self._makeComputer()
    self.computer.edit(allocation_scope='open/personal')
    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_check_computer_state
    self._test_alarm(alarm, self.computer, "Computer_checkState")

  def _test_alarm_check_computer_state_not_selected(self, allocation_scope,
                                                 monitor_scope=None):
    self._makeComputer()
    self.computer.edit(allocation_scope=allocation_scope)
    self.tic()
    if monitor_scope is not None:
      self.computer.edit(monitor_scope=monitor_scope)
      self.tic()

    alarm = self.portal.portal_alarms.\
          slapos_crm_check_computer_state
    self._test_alarm_not_visited(alarm, self.computer, "Computer_checkState")

  def test_alarm_check_computer_state_on_public_computer_with_monitor_scope_disabled(self):
    self._test_alarm_check_computer_state_not_selected(
      allocation_scope='open/public',
      monitor_scope="disabled")

  def test_alarm_check_computer_state_on_friend_computer_with_monitor_scope_disabled(self):
    self._test_alarm_check_computer_state_not_selected(
      allocation_scope='open/friend',
      monitor_scope="disabled")

  def test_alarm_check_computer_state_on_personal_computer_with_monitor_scope_disabled(self):
    self._test_alarm_check_computer_state_not_selected(
      allocation_scope='open/personal',
      monitor_scope="disabled")

  def test_alarm_check_computer_state_closed_forever_computer(self):
    self._test_alarm_check_computer_state_not_selected(
      allocation_scope='closed/forever')

  def test_alarm_check_computer_state_closed_mantainence_computer(self):
    self._test_alarm_check_computer_state_not_selected(
      allocation_scope='closed/maintenance')

  def test_alarm_check_computer_state_closed_termination_computer(self):
    self._test_alarm_check_computer_state_not_selected(
      allocation_scope='closed/termination')


class TestSlapOSCrmMonitoringCheckComputerAllocationScope(SlapOSTestCaseMixinWithAbort):

  def test_alarm_not_allowed_allocation_scope_OpenPublic(self):
    self._makeComputer()
    self.computer.edit(allocation_scope = 'open/public')
    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_check_update_allocation_scope
    self._test_alarm(alarm, self.computer, "Computer_checkAndUpdateAllocationScope")


  def test_alarm_not_allowed_allocation_scope_OpenFriend(self):
    self._makeComputer()
    self.computer.edit(allocation_scope = 'open/friend')
    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_check_update_allocation_scope
    self._test_alarm(alarm, self.computer, "Computer_checkAndUpdateAllocationScope")

  def test_alarm_not_allowed_allocationScope_open_personal(self):
    self._makeComputer()
    self.computer.edit(allocation_scope = 'open/personal')
    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_check_update_allocation_scope
    self._test_alarm_not_visited(alarm, self.computer, "Computer_checkAndUpdateAllocationScope")

class TestSlapOSCrmMonitoringCheckComputerSoftwareInstallation(SlapOSTestCaseMixinWithAbort):

  def test_alarm_run_on_open_public(self):
    self._makeComputer()
    self.computer.edit(allocation_scope = 'open/public')
    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_check_software_installation_state
    self._test_alarm(alarm, self.computer, "Computer_checkSoftwareInstallationState")

  def test_alarm_run_on_open_friend(self):
    self._makeComputer()
    self.computer.edit(allocation_scope = 'open/friend')
    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_check_software_installation_state
    self._test_alarm(alarm, self.computer, "Computer_checkSoftwareInstallationState")


  def test_alarm_run_on_open_personal(self):
    self._makeComputer()
    self.computer.edit(allocation_scope = 'open/personal',
                       monitor_scope="enabled")
    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_check_software_installation_state
    self._test_alarm(alarm, self.computer, "Computer_checkSoftwareInstallationState")

  def test_alarm_dont_run_on_open_public_with_monitor_scope_disabled(self):
    self._makeComputer()
    self.computer.edit(allocation_scope = 'open/public')
    self.tic()
    self.computer.edit(monitor_scope = 'disabled')
    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_check_software_installation_state
    self._test_alarm_not_visited(alarm, self.computer, "Computer_checkSoftwareInstallationState")

  def test_alarm_dont_run_on_open_friend_with_monitor_scope_disabled(self):
    self._makeComputer()
    self.computer.edit(allocation_scope = 'open/friend')
    self.tic()
    self.computer.edit(monitor_scope = 'disabled')
    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_check_software_installation_state
    self._test_alarm_not_visited(alarm, self.computer, "Computer_checkSoftwareInstallationState")

  def test_alarm_dont_run_on_open_personal_with_monitor_scope_disabled(self):
    self._makeComputer()
    self.computer.edit(allocation_scope = 'open/personal',
                       monitor_scope="enabled")
    self.tic()
    self.computer.edit(monitor_scope = 'disabled')
    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_check_software_installation_state
    self._test_alarm_not_visited(alarm, self.computer, "Computer_checkSoftwareInstallationState")

  def _test_alarm_not_run_on_close(self, allocation_scope):
    self._makeComputer()
    self.computer.edit(allocation_scope=allocation_scope)
    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_check_software_installation_state
    self._test_alarm_not_visited(alarm, self.computer, "Computer_checkSoftwareInstallationState")

  def test_alarm_not_run_on_close_forever(self):
    self._test_alarm_not_run_on_close('close/forever')

  def test_alarm_not_run_on_close_maintainence(self):
    self._test_alarm_not_run_on_close('close/maintenence')

  def test_alarm_not_run_on_close_outdated(self):
    self._test_alarm_not_run_on_close('close/outdated')

  def test_alarm_not_run_on_close_termination(self):
    self._test_alarm_not_run_on_close('close/termination')

class TestSlapOSCrmMonitoringCheckComputerPersonalAllocationScope(SlapOSTestCaseMixinWithAbort):

  def test_alarm_allowed_allocation_scope_OpenPersonal_old_computer(self):
    self._makeComputer()
    def getCreationDate(self):
      return DateTime() - 31
    self.computer.edit(allocation_scope = 'open/personal')

    from Products.ERP5Type.Base import Base

    self._simulateScript("Computer_checkAndUpdatePersonalAllocationScope")
    original_get_creation = Base.getCreationDate
    Base.getCreationDate = getCreationDate

    self.tic()

    try:
      self.portal.portal_alarms.slapos_crm_check_update_personal_allocation_scope.activeSense()
      self.tic()
    finally:
      Base.getCreationDate = original_get_creation
      self._dropScript('Computer_checkAndUpdatePersonalAllocationScope')

    self.assertEqual('Visited by Computer_checkAndUpdatePersonalAllocationScope',
      self.computer.workflow_history['edit_workflow'][-1]['comment'])

  @skip('computer creation date is not indexed')
  def test_alarm_allowed_allocation_scope_OpenPersonal_recent_computer(self):
    self._makeComputer()
    def getCreationDate(self):
      return DateTime() - 28
    self.computer.edit(allocation_scope = 'open/personal')

    from Products.ERP5Type.Base import Base

    self._simulateScript("Computer_checkAndUpdatePersonalAllocationScope")
    original_get_creation = Base.getCreationDate
    Base.getCreationDate = getCreationDate

    try:
      self.portal.portal_alarms.slapos_crm_check_update_personal_allocation_scope.activeSense()
      self.tic()
    finally:
      Base.getCreationDate = original_get_creation
      self._dropScript('Computer_checkAndUpdatePersonalAllocationScope')

    self.assertNotEqual('Visited by Computer_checkAndUpdatePersonalAllocationScope',
      self.computer.workflow_history['edit_workflow'][-1]['comment'])

  def test_alarm_allowed_allocation_scope_OpenPersonal_already_closed(self):
    self._makeComputer()
    self.computer.edit(allocation_scope = 'open/oudated')

    self._simulateScript("Computer_checkAndUpdatePersonalAllocationScope")

    try:
      self.portal.portal_alarms.slapos_crm_check_update_personal_allocation_scope.activeSense()
      self.tic()
    finally:
      self._dropScript('Computer_checkAndUpdatePersonalAllocationScope')

    self.assertNotEqual('Visited by Computer_checkAndUpdatePersonalAllocationScope',
      self.computer.workflow_history['edit_workflow'][-1]['comment'])

class TestSlapOSCrmMonitoringCheckInstanceInError(SlapOSTestCaseMixinWithAbort):

  def _makeHostingSubscription(self):
    person = self.portal.person_module.template_member\
         .Base_createCloneDocument(batch_mode=1)
    hosting_subscription = self.portal\
      .hosting_subscription_module.template_hosting_subscription\
      .Base_createCloneDocument(batch_mode=1)
    hosting_subscription.validate()
    new_id = self.generateNewId()
    hosting_subscription.edit(
        title= "Test hosting sub ticket %s" % new_id,
        reference="TESTHST-%s" % new_id,
        destination_section_value=person,
        monitor_scope="enabled"
    )

    return hosting_subscription

  def _makeSoftwareInstance(self, hosting_subscription):

    kw = dict(
      software_release=hosting_subscription.getUrlString(),
      software_type=self.generateNewSoftwareType(),
      instance_xml=self.generateSafeXml(),
      sla_xml=self.generateSafeXml(),
      shared=False,
      software_title=hosting_subscription.getTitle(),
      state='started'
    )
    hosting_subscription.requestStart(**kw)
    hosting_subscription.requestInstance(**kw)

  def test_alarm_check_instance_in_error_validated_hosting_subscription(self):
    host_sub = self._makeHostingSubscription()
    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_check_instance_in_error
    self._test_alarm(alarm, host_sub, "HostingSubscription_checkSoftwareInstanceState")

  def test_alarm_check_instance_in_error_validated_hosting_subscription_with_monitor_disabled(self):
    host_sub = self._makeHostingSubscription()
    host_sub.edit(monitor_scope="disabled")
    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_check_instance_in_error
    self._test_alarm(alarm, host_sub, "HostingSubscription_checkSoftwareInstanceState")

    # This is an un-optimal case, as the query cannot be used in negated form
    # on the searchAndActivate, so we end up callind the script in any situation.
    self.assertEqual('Visited by HostingSubscription_checkSoftwareInstanceState',
      host_sub.workflow_history['edit_workflow'][-1]['comment'])

  def test_alarm_check_instance_in_error_archived_hosting_subscription(self):
    host_sub = self._makeHostingSubscription()
    host_sub.archive()
    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_check_instance_in_error
    self._test_alarm_not_visited(alarm, host_sub, "HostingSubscription_checkSoftwareInstanceState")


class TestSlaposCrmUpdateSupportRequestState(SlapOSTestCaseMixinWithAbort):

  def _makeSupportRequest(self):
    person = self.portal.person_module.template_member\
         .Base_createCloneDocument(batch_mode=1)
    support_request = self.portal.restrictedTraverse(
        self.portal.portal_preferences.getPreferredSupportRequestTemplate()).\
       Base_createCloneDocument(batch_mode=1)
    support_request.validate()
    new_id = self.generateNewId()
    support_request.edit(
        title= "Support Request éçà %s" % new_id, #pylint: disable=invalid-encoded-data
        reference="TESTSRQ-%s" % new_id,
        destination_decision_value=person
    )

    return support_request

  def _makeHostingSubscription(self):
    person = self.portal.person_module.template_member\
         .Base_createCloneDocument(batch_mode=1)
    hosting_subscription = self.portal\
      .hosting_subscription_module.template_hosting_subscription\
      .Base_createCloneDocument(batch_mode=1)
    hosting_subscription.validate()
    new_id = self.generateNewId()
    hosting_subscription.edit(
        title= "Test hosting sub ticket %s" % new_id,
        reference="TESTHST-%s" % new_id,
        destination_section_value=person,
        monitor_scope="enabled"
    )

    return hosting_subscription

  def test_alarm_update_support_request_state(self):
    support_request = self._makeSupportRequest()
    support_request.setResource("service_module/slapos_crm_monitoring")
    hs = self._makeHostingSubscription()
    support_request.setAggregateValue(hs)
    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_update_support_request_state
    self._test_alarm(alarm, support_request, "SupportRequest_updateMonitoringState")
