# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (C) 2013-2021  Nexedi SA and Contributors.
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
  SlapOSTestCaseMixin, SlapOSTestCaseMixinWithAbort
from unittest import skip
from DateTime import DateTime

class TestSlapOSCRMCreateRegularisationRequest(SlapOSTestCaseMixin):

  def test_alarm_expected_person(self):
    new_id = self.generateNewId()
    person = self.portal.person_module.newContent(
      portal_type='Person',
      title="Test person %s" % new_id
      )
    person.validate()

    payment = self.portal.accounting_module.newContent(
      portal_type='Payment Transaction',
      title="Payment Transaction for TestSlapOSCRMCreateRegularisationRequest  person %s" % new_id,
      destination_section=person.getRelativeUrl(),
      start_date=DateTime()
      )
    payment.confirm()
    payment.start()

    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_create_regularisation_request
    self._test_alarm(alarm, person, "Person_checkToCreateRegularisationRequest")

  def test_alarm_not_validated(self):
    new_id = self.generateNewId()
    person = self.portal.person_module.newContent(
      portal_type='Person',
      title="Test person %s" % new_id
      )
    person.validate()
    person.invalidate()

    payment = self.portal.accounting_module.newContent(
      portal_type='Payment Transaction',
      title="Payment Transaction for TestSlapOSCRMCreateRegularisationRequest  person %s" % new_id,
      destination_section=person.getRelativeUrl(),
      start_date=DateTime()
      )
    payment.confirm()
    payment.start()

    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_create_regularisation_request
    self._test_alarm_not_visited(alarm, person, "Person_checkToCreateRegularisationRequest")

  def test_alarm_payment_stopped(self):
    new_id = self.generateNewId()
    person = self.portal.person_module.newContent(
      portal_type='Person',
      title="Test person %s" % new_id
      )
    person.validate()

    payment = self.portal.accounting_module.newContent(
      portal_type='Payment Transaction',
      title="Payment Transaction for TestSlapOSCRMCreateRegularisationRequest  person %s" % new_id,
      destination_section=person.getRelativeUrl(),
      start_date=DateTime()
      )
    payment.confirm()
    payment.start()
    payment.stop()

    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_create_regularisation_request
    self._test_alarm_not_visited(alarm, person, "Person_checkToCreateRegularisationRequest")

  def test_alarm_payment_confirmed(self):
    new_id = self.generateNewId()
    person = self.portal.person_module.newContent(
      portal_type='Person',
      title="Test person %s" % new_id
      )
    person.validate()

    payment = self.portal.accounting_module.newContent(
      portal_type='Payment Transaction',
      title="Payment Transaction for TestSlapOSCRMCreateRegularisationRequest  person %s" % new_id,
      destination_section=person.getRelativeUrl(),
      start_date=DateTime()
      )
    payment.confirm()

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

class TestSlapOSCrmStopInstanceTree(SlapOSTestCaseMixinWithAbort):

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
          slapos_crm_stop_instance_tree
    self._test_alarm(alarm, ticket, "RegularisationRequest_stopInstanceTreeList")

  def test_alarm_matching_regularisation_request_2(self):
    ticket = self.createRegularisationRequest()
    ticket.edit(resource='service_module/slapos_crm_stop_acknowledgement')
    ticket.validate()
    ticket.suspend()

    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_stop_instance_tree
    self._test_alarm(alarm, ticket, "RegularisationRequest_stopInstanceTreeList")

  def test_alarm_not_suspended(self):
    ticket = self.createRegularisationRequest()
    ticket.edit(resource='service_module/slapos_crm_stop_acknowledgement')
    ticket.validate()

    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_stop_instance_tree
    self._test_alarm_not_visited(alarm, ticket, "RegularisationRequest_stopInstanceTreeList")


  def test_alarm_other_resource(self):
    ticket = self.createRegularisationRequest()
    ticket.edit(resource='service_module/slapos_acknowledgement')
    ticket.validate()
    ticket.suspend()

    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_stop_instance_tree
    self._test_alarm_not_visited(alarm, ticket, "RegularisationRequest_stopInstanceTreeList")


class TestSlapOSCrmDeleteInstanceTree(SlapOSTestCaseMixinWithAbort):

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
          slapos_crm_delete_instance_tree
    self._test_alarm(alarm, ticket, "RegularisationRequest_deleteInstanceTreeList")

  def test_alarm_not_suspended(self):
    ticket = self.createRegularisationRequest()
    ticket.edit(resource='service_module/slapos_crm_delete_acknowledgement')
    ticket.validate()

    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_delete_instance_tree
    self._test_alarm_not_visited(alarm, ticket, "RegularisationRequest_deleteInstanceTreeList")


  def test_alarm_other_resource(self):
    ticket = self.createRegularisationRequest()
    ticket.edit(resource='service_module/slapos_crm_delete_reminder')
    ticket.validate()
    ticket.suspend()

    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_delete_instance_tree
    self._test_alarm_not_visited(alarm, ticket, "RegularisationRequest_deleteInstanceTreeList")


class TestSlapOSCrmMonitoringCheckComputeNodeState(SlapOSTestCaseMixinWithAbort):

  def test_alarm_check_public_compute_node_state(self):
    self._makeComputeNode()
    self.compute_node.edit(allocation_scope='open/public')
    self.tic()
    self.assertEqual(self.compute_node.getMonitorScope(), "enabled")
    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_check_compute_node_state
    self._test_alarm(alarm, self.compute_node, "ComputeNode_checkState")

  def test_alarm_check_friend_compute_node_state(self):
    self._makeComputeNode()
    self.compute_node.edit(allocation_scope='open/friend')
    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_check_compute_node_state
    self._test_alarm(alarm, self.compute_node, "ComputeNode_checkState")

  def test_alarm_check_personal_compute_node_state(self):
    self._makeComputeNode()
    self.compute_node.edit(allocation_scope='open/personal')
    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_check_compute_node_state
    self._test_alarm(alarm, self.compute_node, "ComputeNode_checkState")

  def _test_alarm_check_compute_node_state_not_selected(self, allocation_scope,
                                                 monitor_scope=None):
    self._makeComputeNode()
    self.compute_node.edit(allocation_scope=allocation_scope)
    self.tic()
    if monitor_scope is not None:
      self.compute_node.edit(monitor_scope=monitor_scope)
      self.tic()

    alarm = self.portal.portal_alarms.\
          slapos_crm_check_compute_node_state
    self._test_alarm_not_visited(alarm, self.compute_node, "ComputeNode_checkState")

  def test_alarm_check_compute_node_state_on_public_compute_node_with_monitor_scope_disabled(self):
    self._test_alarm_check_compute_node_state_not_selected(
      allocation_scope='open/public',
      monitor_scope="disabled")

  def test_alarm_check_compute_node_state_on_friend_compute_node_with_monitor_scope_disabled(self):
    self._test_alarm_check_compute_node_state_not_selected(
      allocation_scope='open/friend',
      monitor_scope="disabled")

  def test_alarm_check_compute_node_state_on_personal_compute_node_with_monitor_scope_disabled(self):
    self._test_alarm_check_compute_node_state_not_selected(
      allocation_scope='open/personal',
      monitor_scope="disabled")

  def test_alarm_check_compute_node_state_closed_forever_compute_node(self):
    self._test_alarm_check_compute_node_state_not_selected(
      allocation_scope='closed/forever')

  def test_alarm_check_compute_node_state_closed_mantainence_compute_node(self):
    self._test_alarm_check_compute_node_state_not_selected(
      allocation_scope='closed/maintenance')

  def test_alarm_check_compute_node_state_closed_termination_compute_node(self):
    self._test_alarm_check_compute_node_state_not_selected(
      allocation_scope='closed/termination')


class TestSlapOSCrmMonitoringCheckComputeNodeAllocationScope(SlapOSTestCaseMixinWithAbort):

  def test_alarm_not_allowed_allocation_scope_OpenPublic(self):
    self._makeComputeNode()
    self.compute_node.edit(allocation_scope = 'open/public')
    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_check_update_allocation_scope
    self._test_alarm(alarm, self.compute_node, "ComputeNode_checkAndUpdateAllocationScope")


  def test_alarm_not_allowed_allocation_scope_OpenFriend(self):
    self._makeComputeNode()
    self.compute_node.edit(allocation_scope = 'open/friend')
    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_check_update_allocation_scope
    self._test_alarm(alarm, self.compute_node, "ComputeNode_checkAndUpdateAllocationScope")

  def test_alarm_not_allowed_allocationScope_open_personal(self):
    self._makeComputeNode()
    self.compute_node.edit(allocation_scope = 'open/personal')
    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_check_update_allocation_scope
    self._test_alarm_not_visited(alarm, self.compute_node, "ComputeNode_checkAndUpdateAllocationScope")

class TestSlapOSCrmMonitoringCheckComputeNodeSoftwareInstallation(SlapOSTestCaseMixinWithAbort):

  def test_alarm_run_on_open_public(self):
    self._makeComputeNode()
    self.compute_node.edit(allocation_scope = 'open/public')
    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_check_software_installation_state
    self._test_alarm(alarm, self.compute_node, "ComputeNode_checkSoftwareInstallationState")

  def test_alarm_run_on_open_friend(self):
    self._makeComputeNode()
    self.compute_node.edit(allocation_scope = 'open/friend')
    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_check_software_installation_state
    self._test_alarm(alarm, self.compute_node, "ComputeNode_checkSoftwareInstallationState")


  def test_alarm_run_on_open_personal(self):
    self._makeComputeNode()
    self.compute_node.edit(allocation_scope = 'open/personal',
                       monitor_scope="enabled")
    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_check_software_installation_state
    self._test_alarm(alarm, self.compute_node, "ComputeNode_checkSoftwareInstallationState")

  def test_alarm_dont_run_on_open_public_with_monitor_scope_disabled(self):
    self._makeComputeNode()
    self.compute_node.edit(allocation_scope = 'open/public')
    self.tic()
    self.compute_node.edit(monitor_scope = 'disabled')
    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_check_software_installation_state
    self._test_alarm_not_visited(alarm, self.compute_node, "ComputeNode_checkSoftwareInstallationState")

  def test_alarm_dont_run_on_open_friend_with_monitor_scope_disabled(self):
    self._makeComputeNode()
    self.compute_node.edit(allocation_scope = 'open/friend')
    self.tic()
    self.compute_node.edit(monitor_scope = 'disabled')
    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_check_software_installation_state
    self._test_alarm_not_visited(alarm, self.compute_node, "ComputeNode_checkSoftwareInstallationState")

  def test_alarm_dont_run_on_open_personal_with_monitor_scope_disabled(self):
    self._makeComputeNode()
    self.compute_node.edit(allocation_scope = 'open/personal',
                       monitor_scope="enabled")
    self.tic()
    self.compute_node.edit(monitor_scope = 'disabled')
    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_check_software_installation_state
    self._test_alarm_not_visited(alarm, self.compute_node, "ComputeNode_checkSoftwareInstallationState")

  def _test_alarm_not_run_on_close(self, allocation_scope):
    self._makeComputeNode()
    self.compute_node.edit(allocation_scope=allocation_scope)
    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_check_software_installation_state
    self._test_alarm_not_visited(alarm, self.compute_node, "ComputeNode_checkSoftwareInstallationState")

  def test_alarm_not_run_on_close_forever(self):
    self._test_alarm_not_run_on_close('close/forever')

  def test_alarm_not_run_on_close_maintainence(self):
    self._test_alarm_not_run_on_close('close/maintenence')

  def test_alarm_not_run_on_close_outdated(self):
    self._test_alarm_not_run_on_close('close/outdated')

  def test_alarm_not_run_on_close_termination(self):
    self._test_alarm_not_run_on_close('close/termination')

class TestSlapOSCrmMonitoringCheckComputeNodePersonalAllocationScope(SlapOSTestCaseMixinWithAbort):

  def test_alarm_allowed_allocation_scope_OpenPersonal_old_compute_node(self):
    self._makeComputeNode()
    def getCreationDate(self):
      return DateTime() - 31
    self.compute_node.edit(allocation_scope = 'open/personal')

    from Products.ERP5Type.Base import Base

    self._simulateScript("ComputeNode_checkAndUpdatePersonalAllocationScope")
    original_get_creation = Base.getCreationDate
    Base.getCreationDate = getCreationDate

    self.tic()

    try:
      self.portal.portal_alarms.slapos_crm_check_update_personal_allocation_scope.activeSense()
      self.tic()
    finally:
      Base.getCreationDate = original_get_creation
      self._dropScript('ComputeNode_checkAndUpdatePersonalAllocationScope')

    self.assertEqual('Visited by ComputeNode_checkAndUpdatePersonalAllocationScope',
      self.compute_node.workflow_history['edit_workflow'][-1]['comment'])

  @skip('compute node creation date is not indexed')
  def test_alarm_allowed_allocation_scope_OpenPersonal_recent_compute_node(self):
    self._makeComputeNode()
    def getCreationDate(self):
      return DateTime() - 28
    self.compute_node.edit(allocation_scope = 'open/personal')

    from Products.ERP5Type.Base import Base

    self._simulateScript("ComputeNode_checkAndUpdatePersonalAllocationScope")
    original_get_creation = Base.getCreationDate
    Base.getCreationDate = getCreationDate

    try:
      self.portal.portal_alarms.slapos_crm_check_update_personal_allocation_scope.activeSense()
      self.tic()
    finally:
      Base.getCreationDate = original_get_creation
      self._dropScript('ComputeNode_checkAndUpdatePersonalAllocationScope')

    self.assertNotEqual('Visited by ComputeNode_checkAndUpdatePersonalAllocationScope',
      self.compute_node.workflow_history['edit_workflow'][-1]['comment'])

  def test_alarm_allowed_allocation_scope_OpenPersonal_already_closed(self):
    self._makeComputeNode()
    self.compute_node.edit(allocation_scope = 'open/oudated')

    self._simulateScript("ComputeNode_checkAndUpdatePersonalAllocationScope")

    try:
      self.portal.portal_alarms.slapos_crm_check_update_personal_allocation_scope.activeSense()
      self.tic()
    finally:
      self._dropScript('ComputeNode_checkAndUpdatePersonalAllocationScope')

    self.assertNotEqual('Visited by ComputeNode_checkAndUpdatePersonalAllocationScope',
      self.compute_node.workflow_history['edit_workflow'][-1]['comment'])

class TestSlapOSCrmMonitoringCheckInstanceInError(SlapOSTestCaseMixinWithAbort):

  def _makeInstanceTree(self):
    person = self.portal.person_module.template_member\
         .Base_createCloneDocument(batch_mode=1)
    instance_tree = self.portal\
      .instance_tree_module.template_instance_tree\
      .Base_createCloneDocument(batch_mode=1)
    instance_tree.validate()
    new_id = self.generateNewId()
    instance_tree.edit(
        title= "Test hosting sub ticket %s" % new_id,
        reference="TESTHST-%s" % new_id,
        destination_section_value=person,
        monitor_scope="enabled"
    )

    return instance_tree

  def _makeSoftwareInstance(self, instance_tree):

    kw = dict(
      software_release=instance_tree.getUrlString(),
      software_type=self.generateNewSoftwareType(),
      instance_xml=self.generateSafeXml(),
      sla_xml=self.generateSafeXml(),
      shared=False,
      software_title=instance_tree.getTitle(),
      state='started'
    )
    instance_tree.requestStart(**kw)
    instance_tree.requestInstance(**kw)

  def test_alarm_check_instance_in_error_validated_instance_tree(self):
    host_sub = self._makeInstanceTree()
    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_check_instance_in_error
    self._test_alarm(alarm, host_sub, "InstanceTree_checkSoftwareInstanceState")

  def test_alarm_check_instance_in_error_validated_instance_tree_with_monitor_disabled(self):
    host_sub = self._makeInstanceTree()
    host_sub.edit(monitor_scope="disabled")
    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_check_instance_in_error
    self._test_alarm(alarm, host_sub, "InstanceTree_checkSoftwareInstanceState")

    # This is an un-optimal case, as the query cannot be used in negated form
    # on the searchAndActivate, so we end up callind the script in any situation.
    self.assertEqual('Visited by InstanceTree_checkSoftwareInstanceState',
      host_sub.workflow_history['edit_workflow'][-1]['comment'])

  def test_alarm_check_instance_in_error_archived_instance_tree(self):
    host_sub = self._makeInstanceTree()
    host_sub.archive()
    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_check_instance_in_error
    self._test_alarm_not_visited(alarm, host_sub, "InstanceTree_checkSoftwareInstanceState")


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

  def _makeInstanceTree(self):
    person = self.portal.person_module.template_member\
         .Base_createCloneDocument(batch_mode=1)
    instance_tree = self.portal\
      .instance_tree_module.template_instance_tree\
      .Base_createCloneDocument(batch_mode=1)
    instance_tree.validate()
    new_id = self.generateNewId()
    instance_tree.edit(
        title= "Test hosting sub ticket %s" % new_id,
        reference="TESTHST-%s" % new_id,
        destination_section_value=person,
        monitor_scope="enabled"
    )

    return instance_tree

  def test_alarm_update_support_request_state(self):
    support_request = self._makeSupportRequest()
    support_request.setResource("service_module/slapos_crm_monitoring")
    hs = self._makeInstanceTree()
    support_request.setAggregateValue(hs)
    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_update_support_request_state
    self._test_alarm(alarm, support_request, "SupportRequest_updateMonitoringState")
