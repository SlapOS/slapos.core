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
  SlapOSTestCaseMixinWithAbort, simulate, PinnedDateTime, TemporaryAlarmScript
from DateTime import DateTime
import time

class TestSlapOSCrmMonitoringMixin(SlapOSTestCaseMixinWithAbort):

  def assertEventTicket(self, event, ticket, tree_or_node):
    self.assertEqual(event.getFollowUp(), ticket.getRelativeUrl())
    self.assertEqual(event.getSourceProject(), tree_or_node.getFollowUp())
    self.assertEqual(ticket.getSourceProject(), tree_or_node.getFollowUp())
    self.assertEqual(ticket.getCausality(), tree_or_node.getRelativeUrl())
    self.assertEqual(ticket.getSimulationState(), "submitted")
    self.assertEqual(event.getSimulationState(), "delivered")
    self.assertEqual(event.getPortalType(), "Web Message")

  def _makeNotificationMessage(self, reference):
    notification_message = self.portal.notification_message_module.newContent(
      portal_type="Notification Message",
      title='Dummy title',
      text_content='Test NM content<br/>%s<br/>' % reference,
      content_type='text/html',
      )
    return notification_message.getRelativeUrl()

  def _getGeneratedSupportRequest(self, causality_uid):
    support_request_list = self.portal.portal_catalog(
      portal_type='Support Request',
      simulation_state='submitted',
      causality__uid=causality_uid
    )

    self.assertIn(len(support_request_list), [1, 0])
    if len(support_request_list):
      return support_request_list[0]
    return None

  def _makeSupportRequest(self):
    person = self.portal.person_module\
         .newContent(portal_type="Person")
    support_request = self.portal.support_request_module.newContent(
      portal_type="Support Request"
    )
    support_request.submit()
    new_id = self.generateNewId()
    support_request.edit(
        title="Support Request éçà %s" % new_id, #pylint: disable=invalid-encoded-data
        reference="TESTSRQ-%s" % new_id,
        destination_decision_value=person
    )

    return support_request

class TestSlapOSCrmCheckProjectAllocationConsistencyState(TestSlapOSCrmMonitoringMixin):

  ##########################################################################
  # slapos_crm_project_allocation_consistency > ComputeNode_checkProjectAllocationConsistencyState
  ##########################################################################
  def test_ComputeNode_checkProjectAllocationConsistencyState_alarm_remoteNode(self):
    compute_node, _ = self.addComputeNodeAndPartition(self.addProject(),
                                                      portal_type='Remote Node')
    self.tic()
    alarm = self.portal.portal_alarms.slapos_crm_project_allocation_consistency
    self._test_alarm(alarm, compute_node,
             "ComputeNode_checkProjectAllocationConsistencyState")

  def test_ComputeNode_checkProjectAllocationConsistencyState_alarm_monitoredComputeNodeState(self):
    self._makeComputeNode(self.addProject())
    self.tic()
    self.assertEqual(self.compute_node.getMonitorScope(), "enabled")
    alarm = self.portal.portal_alarms.slapos_crm_project_allocation_consistency
    self._test_alarm(alarm, self.compute_node,
             "ComputeNode_checkProjectAllocationConsistencyState")

  def test_ComputeNode_checkProjectAllocationConsistencyState_alarm_close_forever(self):
    self._makeComputeNode(self.addProject())
    # Set close forever disabled monitor
    self.compute_node.edit(allocation_scope='close/forever')
    self.tic()
    self.assertEqual(self.compute_node.getMonitorScope(), "disabled")
    alarm = self.portal.portal_alarms.slapos_crm_project_allocation_consistency
    self._test_alarm_not_visited(alarm, self.compute_node,
                           "ComputeNode_checkProjectAllocationConsistencyState")

  def test_ComputeNode_checkProjectAllocationConsistencyState_alarm_disabledMonitor(self):
    self._makeComputeNode(self.addProject())
    self.compute_node.edit(allocation_scope='open',
                           monitor_scope='disabled')
    self.tic()
    self.login()
    alarm = self.portal.portal_alarms.slapos_crm_project_allocation_consistency
    self._test_alarm_not_visited(alarm, self.compute_node,
                           "ComputeNode_checkProjectAllocationConsistencyState")

  def test_ComputeNode_checkProjectAllocationConsistencyState_alarm_invalidated(self):
    self._makeComputeNode(self.addProject())
    self.compute_node.invalidate()
    self.tic()
    self.login()
    alarm = self.portal.portal_alarms.slapos_crm_project_allocation_consistency
    self._test_alarm_not_visited(alarm, self.compute_node,
                           "ComputeNode_checkProjectAllocationConsistencyState")

  def test_ComputeNode_checkProjectAllocationConsistencyState_alarm_2_node_1_call(self):
    project = self.addProject()
    self._makeComputeNode(project)
    compute_node_a = self.compute_node
    compute_node_a.edit(monitor_scope='enabled')
    self._makeComputeNode(project)
    compute_node_b = self.compute_node
    compute_node_b.edit(monitor_scope='enabled')

    self.assertNotEqual(compute_node_a.getUid(), compute_node_b.getUid())
    self.tic()
    alarm = self.portal.portal_alarms.slapos_crm_project_allocation_consistency
    script_name = "ComputeNode_checkProjectAllocationConsistencyState"
    with TemporaryAlarmScript(self.portal, script_name, attribute=None):
      alarm.activeSense()
      self.tic()
      content_a = compute_node_a.workflow_history['edit_workflow'][-1]['comment']
      content_b = compute_node_b.workflow_history['edit_workflow'][-1]['comment']

      # The alarm should group by project, so only one out of many should reached.
      self.assertNotEqual(content_a, content_b)
      self.assertIn('Visited by %s' % script_name, [content_a, content_b])


class TestSlapOSCrmMonitoringCheckAllocationConsistencyState(TestSlapOSCrmMonitoringMixin):

  def assertAllocationErrorDict(self, error_dict, compute_node, partition,
                                      release_variation, type_variation):
    self.assertNotEqual({}, error_dict)
    self.assertEqual(1, len(error_dict), error_dict)

    type_reference = type_variation.getReference()
    release_url = release_variation.getUrlString()

    _error_dict = error_dict[compute_node.getRelativeUrl()]
    self.assertEqual([release_url], _error_dict.keys())
    self.assertEqual([type_reference], _error_dict[release_url].keys())

    self.assertEqual(partition.getAggregateRelatedValue().getUid(),
      _error_dict[release_url][type_reference][0].getUid())
    self.assertEqual(compute_node.getUid(),
      _error_dict[release_url][type_reference][1].getUid())

  #############################################################################
  # ComputeNode_checkProjectAllocationConsistencyState > ComputeNode_checkAllocationConsistencyState
  #############################################################################
  @simulate('Project_isSupportRequestCreationClosed', '*args, **kwargs', 'return 0')
  def test_ComputeNode_checkAllocationConsistencyState_script_noAllocationCell(self):
    with PinnedDateTime(self, DateTime() - 1.1):
      _, \
        release_variation, \
        type_variation, \
        compute_node, \
        partition, \
        _ = self.bootstrapAllocableInstanceTree(allocation_state='allocated')

      self.tic()

    ticket = compute_node.ComputeNode_checkAllocationConsistencyState()

    # Double check error dict
    error_dict = partition.ComputePartition_checkAllocationConsistencyState()
    self.assertAllocationErrorDict(error_dict, compute_node, partition,
                                   release_variation, type_variation)
    ticket_title = "%s has missing allocation supplies." % compute_node.getTitle()
    self.assertNotEqual(ticket, None)
    self.assertEqual(ticket.getTitle(), ticket_title)

    self.tic()
    event_list = ticket.getFollowUpRelatedValueList()
    self.assertEqual(len(event_list), 1)
    event = event_list[0]

    self.assertIn("The following contains instances that has Software Releases/Types",
                  event.getTextContent())

    self.assertIn(release_variation.getUrlString(), event.getTextContent())
    self.assertIn(type_variation.getReference(), event.getTextContent())
    self.assertEventTicket(event, ticket, compute_node)

  @simulate('Project_isSupportRequestCreationClosed', '*args, **kwargs', 'return 0')
  def test_ComputeNode_checkAllocationConsistencyState_script_hasTicketAlready(self):
    with PinnedDateTime(self, DateTime() - 1.1):
      _, \
        release_variation, \
        type_variation, \
        compute_node, \
        partition, \
        _ = self.bootstrapAllocableInstanceTree(allocation_state='allocated')

      project = compute_node.getFollowUpValue()
      title = "checkAllocationConsistencyState %s" % self.generateNewId()
      support_request = project.Project_createTicketWithCausality(
        "Support Request", title, title,
        causality=compute_node.getRelativeUrl(),
        destination_decision=project.getDestination()
      )
      self.assertNotEqual(support_request, None)
      self.tic()

    ticket = compute_node.ComputeNode_checkAllocationConsistencyState()
    self.assertEqual(ticket, None)

    # Double check error dict exists despite ticket isnt created.
    error_dict = partition.ComputePartition_checkAllocationConsistencyState()
    self.assertAllocationErrorDict(error_dict, compute_node, partition,
                                   release_variation, type_variation)

  @simulate('Project_isSupportRequestCreationClosed', '*args, **kwargs', 'return 0')
  def test_ComputeNode_checkAllocationConsistencyState_script_ongoingUpgrade(self):
    with PinnedDateTime(self, DateTime() - 1.1):
      _, _, _, \
        compute_node, \
        partition, \
        instance_tree = self.bootstrapAllocableInstanceTree(allocation_state='allocated')

      ud = self.portal.upgrade_decision_module.newContent(
        portal_type="Upgrade Decision",
        aggregate_value=instance_tree)
      ud.plan()

      self.tic()

    ticket = compute_node.ComputeNode_checkAllocationConsistencyState()

    # Double check error dict
    error_dict = partition.ComputePartition_checkAllocationConsistencyState()
    self.assertEqual({}, error_dict)
    self.assertEqual(None, ticket)

  @simulate('Project_isSupportRequestCreationClosed', '*args, **kwargs', 'return 1')
  def test_ComputeNode_checkAllocationConsistencyState_script_creationClosed(self):
    with PinnedDateTime(self, DateTime() - 1.1):
      _, _, _, compute_node, \
        _, _ = self.bootstrapAllocableInstanceTree(allocation_state='allocated')

      self.tic()

    ticket = compute_node.ComputeNode_checkAllocationConsistencyState()
    self.assertEqual(None, ticket)

  @simulate('Project_isSupportRequestCreationClosed', '*args, **kwargs', 'return 0')
  def test_ComputeNode_checkAllocationConsistencyState_script_monitorDisabled(self):
    with PinnedDateTime(self, DateTime() - 1.1):
      _, _, _, compute_node, \
        _, _ = self.bootstrapAllocableInstanceTree(allocation_state='allocated')

      compute_node.setMonitorScope('disabled')
      self.tic()

    ticket = compute_node.ComputeNode_checkAllocationConsistencyState()
    self.assertEqual(None, ticket)

  @simulate('Project_isSupportRequestCreationClosed', '*args, **kwargs', 'return 0')
  def test_ComputeNode_checkAllocationConsistencyState_script_RemotenoAllocationCell(self):
    with PinnedDateTime(self, DateTime() - 1.1):
      _, release_variation, \
        type_variation, \
        compute_node, \
        partition, \
        _ = self.bootstrapAllocableInstanceTree(
          allocation_state='allocated', node='remote', shared=True)

      self.tic()

    ticket = compute_node.ComputeNode_checkAllocationConsistencyState()

    # Double check error dict
    error_dict = partition.ComputePartition_checkAllocationConsistencyState()
    self.assertAllocationErrorDict(error_dict, compute_node, partition,
                                   release_variation, type_variation)

    ticket_title = "%s has missing allocation supplies." % compute_node.getTitle()
    self.assertNotEqual(ticket, None)
    self.assertEqual(ticket.getTitle(), ticket_title)

    self.tic()
    event_list = ticket.getFollowUpRelatedValueList()
    self.assertEqual(len(event_list), 1)
    event = event_list[0]

    self.assertIn("The following contains instances that has Software Releases/Types",
                  event.getTextContent())

    self.assertIn(release_variation.getUrlString(), event.getTextContent())
    self.assertIn(type_variation.getReference(), event.getTextContent())
    self.assertEventTicket(event, ticket, compute_node)

  @simulate('Project_isSupportRequestCreationClosed', '*args, **kwargs', 'return 0')
  def test_ComputeNode_checkAllocationConsistencyState_script_InstanceNodenoAllocationCell(self):
    with PinnedDateTime(self, DateTime() - 1.1):
      _, release_variation, \
        type_variation, \
        instance_node, \
        partition, \
        _ = self.bootstrapAllocableInstanceTree(
          allocation_state='allocated', node='instance', shared=True)

      self.tic()

    compute_node = partition.getParentValue()
    self.assertEqual(compute_node.getPortalType(), 'Compute Node')

    ticket = compute_node.ComputeNode_checkAllocationConsistencyState()

    # Double check error dict
    error_dict = partition.ComputePartition_checkAllocationConsistencyState()

    self.assertNotEqual({}, error_dict)
    self.assertEqual(2, len(error_dict), error_dict)

    # Type refers to slave instance type
    type_reference = type_variation.getReference()
    release_url = release_variation.getUrlString()

    # Check first missing allocation supply for the instance on the computer
    _error_dict = error_dict[compute_node.getRelativeUrl()]


    software_instance = partition.getAggregateRelatedValue(
      portal_type="Software Instance")
    self.assertEqual([release_url], _error_dict.keys())
    instance_software_type = software_instance.getSourceReference()
    self.assertEqual([instance_software_type],
                     _error_dict[release_url].keys())

    self.assertEqual(software_instance.getRelativeUrl(),
      _error_dict[release_url][instance_software_type][0].getRelativeUrl())
    self.assertEqual(compute_node.getRelativeUrl(),
      _error_dict[release_url][instance_software_type][1].getRelativeUrl())

    for _index in error_dict:
      if _index != compute_node.getRelativeUrl():
        instance_error_dict = error_dict[_index]

    slave_instance = partition.getAggregateRelatedValue(portal_type='Slave Instance')
    self.assertEqual([release_url], instance_error_dict.keys())
    self.assertEqual([type_reference],  instance_error_dict[release_url].keys())

    self.assertEqual(slave_instance.getSourceReference(), type_reference)
    self.assertEqual(slave_instance.getRelativeUrl(),
      instance_error_dict[release_url][type_reference][0].getRelativeUrl())
    self.assertNotEqual(compute_node.getRelativeUrl(),
      instance_error_dict[release_url][type_reference][1].getRelativeUrl())

    instance_node = instance_error_dict[release_url][type_reference][1]
    self.assertEqual(instance_node.getPortalType(), 'Instance Node')

    ticket_title = "%s has missing allocation supplies." % compute_node.getTitle()
    self.assertNotEqual(ticket, None)
    self.assertEqual(ticket.getTitle(), ticket_title)

    self.tic()
    event_list = ticket.getFollowUpRelatedValueList()
    self.assertEqual(len(event_list), 1)
    event = event_list[0]

    self.assertIn("The following contains instances that has Software Releases/Types",
                  event.getTextContent())

    self.assertIn(release_variation.getUrlString(), event.getTextContent())
    self.assertIn(type_variation.getReference(), event.getTextContent())
    self.assertEventTicket(event, ticket, compute_node)



class TestSlapOSCrmMonitoringCheckComputeNodeProjectState(TestSlapOSCrmMonitoringMixin):

  ##########################################################################
  # slapos_crm_monitoring_project > ComputeNode_checkMonitoringState
  ##########################################################################
  def test_ComputeNode_checkProjectMontoringState_alarm_remoteNode(self):
    compute_node, _ = self.addComputeNodeAndPartition(self.addProject(), portal_type='Remote Node')
    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_monitoring_project
    self._test_alarm(alarm, compute_node, "ComputeNode_checkProjectMontoringState")

  def test_ComputeNode_checkProjectMontoringState_alarm_monitoredComputeNodeState(self):
    self._makeComputeNode(self.addProject())
    self.tic()
    self.assertEqual(self.compute_node.getMonitorScope(), "enabled")
    alarm = self.portal.portal_alarms.\
          slapos_crm_monitoring_project
    self._test_alarm(alarm, self.compute_node, "ComputeNode_checkProjectMontoringState")

  def test_ComputeNode_checkProjectMontoringState_alarm_close_forever(self):
    self._makeComputeNode(self.addProject())
    # Set close forever disabled monitor
    self.compute_node.edit(allocation_scope='close/forever')
    self.tic()
    self.assertEqual(self.compute_node.getMonitorScope(), "disabled")
    alarm = self.portal.portal_alarms.\
          slapos_crm_monitoring_project
    self._test_alarm_not_visited(alarm, self.compute_node, "ComputeNode_checkProjectMontoringState")

  def test_ComputeNode_checkProjectMontoringState_alarm_disabledMonitor(self):
    self._makeComputeNode(self.addProject())
    self.compute_node.edit(allocation_scope='open',
                           monitor_scope='disabled')
    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_monitoring_project
    self._test_alarm_not_visited(alarm, self.compute_node, "ComputeNode_checkProjectMontoringState")

  def test_ComputeNode_checkProjectMontoringState_alarm_invalidated(self):
    self._makeComputeNode(self.addProject())
    self.compute_node.invalidate()
    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_monitoring_project
    self._test_alarm_not_visited(alarm, self.compute_node, "ComputeNode_checkProjectMontoringState")

  def test_ComputeNode_checkProjectMontoringState_alarm_2_node_1_call(self):
    project = self.addProject()
    self._makeComputeNode(project)
    compute_node_a = self.compute_node
    compute_node_a.edit(monitor_scope='enabled')
    self._makeComputeNode(project)
    compute_node_b = self.compute_node
    compute_node_b.edit(monitor_scope='enabled')

    self.assertNotEqual(compute_node_a.getUid(), compute_node_b.getUid())
    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_monitoring_project

    script_name = "ComputeNode_checkProjectMontoringState"
    with TemporaryAlarmScript(self.portal, script_name, attribute=None):
      alarm.activeSense()
      self.tic()
      content_a = compute_node_a.workflow_history['edit_workflow'][-1]['comment']
      content_b = compute_node_b.workflow_history['edit_workflow'][-1]['comment']

      # The alarm should group by project, so only one out of many should reached.
      self.assertNotEqual(content_a, content_b)
      self.assertIn('Visited by %s' % script_name, [content_a, content_b])

class TestSlapOSCrmMonitoringCheckComputeNodeState(TestSlapOSCrmMonitoringMixin):

  ##########################################################################
  # ComputeNode_checkProjectMontoringState > ComputeNode_checkMonitoringState
  ##########################################################################
  @simulate('Project_isSupportRequestCreationClosed', '*args, **kwargs', 'return 0')
  def test_ComputeNode_checkMonitoringState_script_oldAccessStatus(self):
    compute_node, _ = self._makeComputeNode(self.addProject())
    d = DateTime() - 1.1
    with PinnedDateTime(self, d):
      compute_node.setAccessStatus("")

    compute_node_support_request = compute_node.ComputeNode_checkMonitoringState()

    self.assertIn("Lost contact with compute_node",
      compute_node_support_request.getTitle())
    self.assertIn("has not contacted the server for more than 30 minutes",
      compute_node_support_request.getDescription())
    self.assertIn(d.strftime("%Y/%m/%d %H:%M:%S"),
      compute_node_support_request.getDescription())

  @simulate('Project_isSupportRequestCreationClosed', '*args, **kwargs', 'return 0')
  def test_ComputeNode_checkMonitoringState_script_noAccessStatus(self):
    compute_node, _ = self._makeComputeNode(self.addProject())
    compute_node_support_request = compute_node.ComputeNode_checkMonitoringState()

    self.assertIn("Lost contact with compute_node",
      compute_node_support_request.getTitle())
    self.assertIn("has not contacted the server (No Contact Information)",
      compute_node_support_request.getDescription())


  @simulate('Project_isSupportRequestCreationClosed', '*args, **kwargs', 'return 0')
  @simulate('NotificationTool_getDocumentValue',
            'reference=None, **kw',
  'assert reference == "slapos-crm-compute_node_check_state.notification", reference\n' \
  'return context.restrictedTraverse(' \
  'context.REQUEST["test_ComputeNode_checkMonitoringState_notify"])')
  def test_ComputeNode_checkMonitoringState_script_notify(self):
    compute_node, _ = self._makeComputeNode(self.addProject())

    with PinnedDateTime(self, DateTime() - 1.1):
      compute_node.setAccessStatus("")

    self.portal.REQUEST['test_ComputeNode_checkMonitoringState_notify'] = \
        self._makeNotificationMessage(compute_node.getReference())

    compute_node.ComputeNode_checkMonitoringState()
    self.tic()

    ticket_title = "Lost contact with compute_node %s" % compute_node.getReference()
    ticket = self._getGeneratedSupportRequest(compute_node.getUid())

    self.assertNotEqual(ticket, None)
    self.assertEqual(ticket.getTitle(), ticket_title)

    event_list = ticket.getFollowUpRelatedValueList()
    self.assertEqual(len(event_list), 1)
    event = event_list[0]

    self.assertEqual(
      event.getTitle(),
      self.portal.restrictedTraverse(
        self.portal.REQUEST['test_ComputeNode_checkMonitoringState_notify']
      ).getTitle()
    )
    self.assertIn(compute_node.getReference(), event.getTextContent())
    self.assertEventTicket(event, ticket, compute_node)

  @simulate('Project_isSupportRequestCreationClosed', '*args, **kwargs', 'return 0')
  @simulate('NotificationTool_getDocumentValue',
            'reference=None, **kw',
  'assert reference == "slapos-crm-compute_node_check_state.notification"\n' \
  'return context.restrictedTraverse(' \
  'context.REQUEST["test_ComputeNode_checkMonitoringState_empty_cache_notify"])')
  def test_ComputeNode_checkMonitoringState_script_emptyCacheNotify(self):
    compute_node, _ = self._makeComputeNode(self.addProject())

    self.portal.REQUEST['test_ComputeNode_checkMonitoringState_empty_cache_notify'] = \
        self._makeNotificationMessage(compute_node.getReference())

    error_dict = compute_node.ComputeNode_getReportedErrorDict()
    compute_node.ComputeNode_checkMonitoringState()
    self.tic()

    ticket_title = "Lost contact with compute_node %s" % compute_node.getReference()
    ticket = self._getGeneratedSupportRequest(compute_node.getUid())
    self.assertNotEqual(ticket, None)
    self.assertEqual(ticket_title, error_dict['ticket_title'])
    self.assertEqual(ticket_title, ticket.getTitle())

    message = ticket.SupportRequest_recheckMonitoring()
    self.assertEqual(error_dict['message'], message)
    self.assertEqual("No Contact Information", message)

    event_list = ticket.getFollowUpRelatedValueList()
    self.assertEqual(len(event_list), 1)
    event = event_list[0]

    self.assertEqual(
      event.getTitle(),
      self.portal.restrictedTraverse(
        self.portal.REQUEST['test_ComputeNode_checkMonitoringState_empty_cache_notify']
      ).getTitle()
    )
    self.assertIn(compute_node.getReference(), event.getTextContent())
    self.assertEventTicket(event, ticket, compute_node)


    compute_node.setAccessStatus("")
    message = ticket.SupportRequest_recheckMonitoring()
    self.assertEqual(None, message)

  @simulate('Project_isSupportRequestCreationClosed', '*args, **kwargs', 'return 0')
  @simulate('NotificationTool_getDocumentValue',
            'reference=None, **kw',
  'assert reference == "slapos-crm-compute_node_check_stalled_instance_state.notification", reference\n' \
  'return context.restrictedTraverse(' \
  'context.REQUEST["test_ComputeNode_checkMonitoringState_stalled_instance"])')
  def test_ComputeNode_checkMonitoringState_script_stalledInstance(self):
    project = self.addProject()
    compute_node, _ = self._makeComputeNode(project)
    self._makeComplexComputeNode(project)
    compute_node = self.compute_node

    self.portal.REQUEST['test_ComputeNode_checkMonitoringState_stalled_instance'] = \
        self._makeNotificationMessage(compute_node.getReference())

    # Computer is getting access
    compute_node.setAccessStatus("")

    with PinnedDateTime(self, DateTime() - 1.1):
      self.start_requested_software_instance.setAccessStatus("")

    error_dict = compute_node.ComputeNode_getReportedErrorDict()
    compute_node.ComputeNode_checkMonitoringState()
    self.tic()

    ticket_title = "Compute Node %s has a stalled instance process" % compute_node.getReference()
    ticket = self._getGeneratedSupportRequest(compute_node.getUid())
    self.assertNotEqual(ticket, None)
    self.assertEqual(ticket_title, error_dict['ticket_title'])
    self.assertEqual(ticket_title, ticket.getTitle())

    message = ticket.SupportRequest_recheckMonitoring()
    self.assertEqual(error_dict['message'], message)
    self.assertEqual(message,
        "%s has a stalled instance process" % compute_node.getReference())


    event_list = ticket.getFollowUpRelatedValueList()
    self.assertEqual(len(event_list), 1)
    event = event_list[0]

    self.assertEqual(
      event.getTitle(),
      self.portal.restrictedTraverse(
        self.portal.REQUEST['test_ComputeNode_checkMonitoringState_stalled_instance']
      ).getTitle()
    )
    self.assertIn(compute_node.getReference(), event.getTextContent())
    self.assertEventTicket(event, ticket, compute_node)

    self.start_requested_software_instance.setAccessStatus("")

    message = ticket.SupportRequest_recheckMonitoring()
    self.assertEqual(message, None)

  @simulate('Project_isSupportRequestCreationClosed', '*args, **kwargs', 'return 0')
  @simulate('NotificationTool_getDocumentValue',
            'reference=None, **kw',
  'assert reference == "slapos-crm-compute_node_check_stalled_instance_state.notification", reference\n' \
  'return context.restrictedTraverse(' \
  'context.REQUEST["test_ComputeNode_checkMonitoringState_stalled_instance"])')
  def test_ComputeNode_checkMonitoringState_script_stalledInstanceSingle(self):
    project = self.addProject()
    compute_node, _ = self._makeComputeNode(project)
    self._makeComplexComputeNode(project)
    compute_node = self.compute_node

    self.portal.REQUEST['test_ComputeNode_checkMonitoringState_stalled_instance'] = \
        self._makeNotificationMessage(compute_node.getReference())

    # Computer is getting access
    compute_node.setAccessStatus("")

    with PinnedDateTime(self, DateTime() - 1.1):
      self.start_requested_software_instance.setAccessStatus("")
      self.start_requested_software_installation.setAccessStatus("")

    error_dict = compute_node.ComputeNode_getReportedErrorDict()
    compute_node.ComputeNode_checkMonitoringState()
    self.tic()

    ticket_title = "Compute Node %s has a stalled instance process" % compute_node.getReference()
    ticket = self._getGeneratedSupportRequest(compute_node.getUid())
    self.assertNotEqual(ticket, None)
    self.assertEqual(ticket_title, error_dict['ticket_title'])
    self.assertEqual(ticket_title, ticket.getTitle())

    message = ticket.SupportRequest_recheckMonitoring()
    self.assertEqual(error_dict['message'], message)
    self.assertEqual(message,
       "%s has a stalled instance process" % compute_node.getReference())

    event_list = ticket.getFollowUpRelatedValueList()
    self.assertEqual(len(event_list), 1)
    event = event_list[0]

    self.assertEqual(
      event.getTitle(),
      self.portal.restrictedTraverse(
        self.portal.REQUEST['test_ComputeNode_checkMonitoringState_stalled_instance']
      ).getTitle()
    )
    self.assertIn(compute_node.getReference(), event.getTextContent())
    self.assertEventTicket(event, ticket, compute_node)


    self.start_requested_software_instance.setAccessStatus("")
    self.start_requested_software_installation.setAccessStatus("")

    message = ticket.SupportRequest_recheckMonitoring()
    self.assertEqual(message, None)

  @simulate('Project_isSupportRequestCreationClosed', '*args, **kwargs', 'return 0')
  @simulate('NotificationTool_getDocumentValue',
            'reference=None, **kw',
  'assert reference == "slapos-crm-compute_node_check_modified_file.notification", reference\n' \
  'return context.restrictedTraverse(' \
  'context.REQUEST["test_ComputeNode_checkMonitoringState_script_modificationArray"])')
  @simulate('ComputeNode_hasModifiedFile', '**kw',
  'return context.restrictedTraverse(' \
  'context.REQUEST["test_ComputeNode_checkMonitoringState_data_array"])')
  def test_ComputeNode_checkMonitoringState_script_modificationArray(self):
    project = self.addProject()
    compute_node, _ = self._makeComputeNode(project)
    self._makeComplexComputeNode(project)
    compute_node = self.compute_node

    self.portal.REQUEST['test_ComputeNode_checkMonitoringState_script_modificationArray'] = \
        self._makeNotificationMessage(compute_node.getReference())

    data_array = self.portal.data_array_module.newContent(
      portal_type="Data Array",
      reference='test-data-array-%s' % self.generateNewId()
    )

    self.portal.REQUEST['test_ComputeNode_checkMonitoringState_data_array'] = \
        data_array.getRelativeUrl()

    # Computer is getting access
    compute_node.setAccessStatus("")

    error_dict = compute_node.ComputeNode_getReportedErrorDict()
    compute_node.ComputeNode_checkMonitoringState()
    self.tic()

    ticket_title = "Compute Node %s has modified file" % compute_node.getReference()
    ticket = self._getGeneratedSupportRequest(compute_node.getUid())
    self.assertNotEqual(ticket, None)
    self.assertEqual(ticket_title, error_dict['ticket_title'])
    self.assertEqual(ticket_title, ticket.getTitle())

    message = ticket.SupportRequest_recheckMonitoring()
    self.assertEqual(error_dict['message'], message)
    self.assertEqual("%s has modified file" % compute_node.getReference(),
                     message)

    event_list = ticket.getFollowUpRelatedValueList()
    self.assertEqual(len(event_list), 1)
    event = event_list[0]

    self.assertEqual(
      event.getTitle(),
      self.portal.restrictedTraverse(
        self.portal.REQUEST['test_ComputeNode_checkMonitoringState_script_modificationArray']
      ).getTitle()
    )
    self.assertIn(compute_node.getReference(), event.getTextContent())
    self.assertEventTicket(event, ticket, compute_node)

  @simulate('Project_isSupportRequestCreationClosed', '*args, **kwargs', 'return 0')
  def test_ComputeNode_checkMonitoringState_installation_no_information(self):
    with PinnedDateTime(self, DateTime() - 1.1):
      project = self.addProject()
      compute_node, _ = self._makeComputeNode(project)
      self._makeComplexComputeNode(project)
      compute_node = self.compute_node

    # Computer and instances are accessed
    compute_node.setAccessStatus("")
    self.start_requested_software_instance.setAccessStatus("")
    self.tic()

    error_dict = compute_node.ComputeNode_getReportedErrorDict()
    compute_node.ComputeNode_checkMonitoringState()
    self.tic()

    # No ticket at all is created
    ticket = self._getGeneratedSupportRequest(compute_node.getUid())
    self.assertEqual(error_dict['ticket_title'], None)
    self.assertEqual(ticket, None)


  @simulate('Project_isSupportRequestCreationClosed', '*args, **kwargs', 'return 0')
  def test_ComputeNode_checkMonitoringState_installation_oldBuild(self):
    with PinnedDateTime(self, DateTime() - 1.1):
      project = self.addProject()
      compute_node, _ = self._makeComputeNode(project)
      self._makeComplexComputeNode(project)
      compute_node = self.compute_node
      self.start_requested_software_installation.setAccessStatus("")

    # Computer and instances are accessed
    compute_node.setAccessStatus("")
    self.start_requested_software_instance.setAccessStatus("")
    self.tic()

    error_dict = compute_node.ComputeNode_getReportedErrorDict()
    compute_node.ComputeNode_checkMonitoringState()
    self.tic()

    # No ticket at all is created
    ticket = self._getGeneratedSupportRequest(compute_node.getUid())
    self.assertEqual(error_dict['ticket_title'], None)
    self.assertEqual(ticket, None)

  @simulate('Project_isSupportRequestCreationClosed', '*args, **kwargs', 'return 0')
  def test_ComputeNode_checkMonitoringState_installation_recentBuild(self):
    project = self.addProject()
    self._makeComputeNode(project)
    self._makeComplexComputeNode(project)
    compute_node = self.compute_node

    # Computer and instances are accessed fine.
    compute_node.setAccessStatus("")
    self.start_requested_software_instance.setAccessStatus("")
    self.start_requested_software_installation.setBuildingStatus("building")
    self.tic()

    error_dict = compute_node.ComputeNode_getReportedErrorDict()
    compute_node.ComputeNode_checkMonitoringState()
    self.tic()

    ticket = self._getGeneratedSupportRequest(compute_node.getUid())
    self.assertEqual(None, error_dict['ticket_title'])
    self.assertEqual(ticket, None)

  @simulate('Project_isSupportRequestCreationClosed', '*args, **kwargs', 'return 0')
  @simulate('NotificationTool_getDocumentValue',
            'reference=None, **kw',
  'assert reference == "slapos-crm-compute_node_software_installation_state.notification", reference\n' \
  'return context.restrictedTraverse(' \
  'context.REQUEST["test_ComputeNode_checkMonitoringState_notify"])')
  def test_ComputeNode_checkMonitoringState_installation_notifySlow(self):
    with PinnedDateTime(self, DateTime() - 1.1):
      project = self.addProject()
      self._makeComputeNode(project)
      self._makeComplexComputeNode(project)
      compute_node = self.compute_node

    # Computer and instances are accessed fine.
    compute_node.setAccessStatus("")
    self.start_requested_software_instance.setAccessStatus("")
    self.start_requested_software_installation.setBuildingStatus("building")
    self.tic()
    self.portal.REQUEST['test_ComputeNode_checkMonitoringState_notify'] = \
        self._makeNotificationMessage(compute_node.getReference())

    error_dict = compute_node.ComputeNode_getReportedErrorDict()
    compute_node.ComputeNode_checkMonitoringState()
    self.tic()

    ticket_title = "%s is failing or taking too long to build on %s" % (
      self.start_requested_software_installation.getReference(),
      compute_node.getReference()
    )

    ticket = self._getGeneratedSupportRequest(compute_node.getUid())
    self.assertNotEqual(ticket, None)
    self.assertEqual(ticket_title, error_dict['ticket_title'])
    self.assertEqual(ticket_title, ticket.getTitle())

    message = ticket.SupportRequest_recheckMonitoring()
    self.assertEqual(error_dict['message'], message)
    self.assertIn(" is building for mode them 12 hours on", message)

    event_list = ticket.getFollowUpRelatedValueList()
    self.assertEqual(len(event_list), 1)
    event = event_list[0]

    self.assertEqual(
      event.getTitle(),
      self.portal.restrictedTraverse(
        self.portal.REQUEST['test_ComputeNode_checkMonitoringState_notify']
      ).getTitle()
    )
    self.assertIn(compute_node.getReference(), event.getTextContent())
    self.assertEventTicket(event, ticket, compute_node)

  @simulate('Project_isSupportRequestCreationClosed', '*args, **kwargs', 'return 0')
  @simulate('NotificationTool_getDocumentValue',
            'reference=None, **kw',
  'assert reference == "slapos-crm-compute_node_software_installation_state.notification", reference\n' \
  'return context.restrictedTraverse(' \
  'context.REQUEST["test_ComputeNode_checkMonitoringState_notify"])')
  def test_ComputeNode_checkMonitoringState_installation_notifyError(self):
    with PinnedDateTime(self, DateTime() - 1.1):
      project = self.addProject()
      compute_node, _ = self._makeComputeNode(project)
      self._makeComplexComputeNode(project)
      compute_node = self.compute_node

    self.start_requested_software_installation.setErrorStatus("")
    self.portal.REQUEST['test_ComputeNode_checkMonitoringState_notify'] = \
        self._makeNotificationMessage(compute_node.getReference())

    # Computer and instances are accessed fine.
    compute_node.setAccessStatus("")
    self.start_requested_software_instance.setAccessStatus("")
    self.tic()

    error_dict = compute_node.ComputeNode_getReportedErrorDict()
    compute_node.ComputeNode_checkMonitoringState()

    self.tic()
    ticket_title = "%s is failing or taking too long to build on %s" % (
      self.start_requested_software_installation.getReference(),
      compute_node.getReference()
    )
    ticket = self._getGeneratedSupportRequest(compute_node.getUid())

    self.assertNotEqual(ticket, None)
    self.assertEqual(error_dict['ticket_title'], ticket_title)
    self.assertEqual(ticket.getTitle(), ticket_title)

    message = ticket.SupportRequest_recheckMonitoring()
    self.assertEqual(error_dict['message'], message)
    self.assertIn(" is failing to build for too long on", message)

    event_list = ticket.getFollowUpRelatedValueList()
    self.assertEqual(len(event_list), 1)
    event = event_list[0]

    self.assertEqual(
      event.getTitle(),
      self.portal.restrictedTraverse(
        self.portal.REQUEST['test_ComputeNode_checkMonitoringState_notify']
      ).getTitle()
    )
    self.assertIn(compute_node.getReference(), event.getTextContent())
    self.assertEventTicket(event, ticket, compute_node)

class TestSlapOSCrmSoftwareInstance_checkInstanceTreeMonitoringState(TestSlapOSCrmMonitoringMixin):

  @simulate('Project_isSupportRequestCreationClosed', '*args, **kwargs', 'return 0')
  def test_SoftwareInstance_checkInstanceTreeMonitoringState_alarm_not_called(self):
    project = self.addProject()
    self._makeComputeNode(project)
    self._makeComplexComputeNode(project)

    # Computer and instances are accessed fine.
    self.compute_node.setMonitorScope("disabled")
    self.compute_node.setAccessStatus("")
    self.start_requested_software_instance.setAccessStatus("")
    self.tic()
    self.assertEqual(self.compute_node.getMonitorScope(), "disabled")
    alarm = self.portal.portal_alarms.slapos_crm_monitoring_project
    self._test_alarm_not_visited(alarm,
      self.start_requested_software_instance,
      "SoftwareInstance_checkInstanceTreeMonitoringState")


  @simulate('Project_isSupportRequestCreationClosed', '*args, **kwargs', 'return 0')
  def test_SoftwareInstance_checkInstanceTreeMonitoringState_alarm_instance(self):
    project = self.addProject()
    self._makeComputeNode(project)
    self._makeComplexComputeNode(project)

    # Computer and instances are accessed fine.
    self.compute_node.setMonitorScope("enabled")
    self.compute_node.setAccessStatus("")
    self.start_requested_software_instance.setAccessStatus("")
    self.tic()
    self.assertEqual(self.compute_node.getMonitorScope(), "enabled")
    alarm = self.portal.portal_alarms.slapos_crm_monitoring_project

    self._test_alarm(alarm,
      self.start_requested_software_instance,
      "SoftwareInstance_checkInstanceTreeMonitoringState")

  @simulate('Project_isSupportRequestCreationClosed', '*args, **kwargs', 'return 0')
  def test_SoftwareInstance_checkInstanceTreeMonitoringState_alarm_2_instance_1_call(self):
    project = self.addProject()
    self._makeComputeNode(project)
    self._makeComplexComputeNode(project)

    # Computer and instances are accessed fine.
    self.compute_node.setMonitorScope("enabled")
    self.compute_node.setAccessStatus("")
    self.start_requested_software_instance.setAccessStatus("")

    self.login(self.start_requested_software_instance.getUserId())

    # Atach one more software instances
    instance_kw = dict(
      software_release='http://a.release',
      software_type='type',
      instance_xml=self.generateSafeXml(),
      sla_xml=self.generateSafeXml(),
      shared=False,
      software_title='Instance0',
      state='started'
    )
    self.start_requested_software_instance.requestInstance(**instance_kw)
    self.tic()
    self.login()

    instance_a = self.start_requested_software_instance
    instance_b = instance_a.getSuccessorValue(portal_type="Software Instance")
    self.assertEqual(instance_a.getFollowUpUid(), project.getUid())
    self.assertEqual(instance_b.getFollowUpUid(), project.getUid())
    self.assertEqual(instance_a.getSpecialise(), instance_b.getSpecialise())
    self.assertEqual(self.compute_node.getMonitorScope(), "enabled")
    alarm = self.portal.portal_alarms.slapos_crm_monitoring_project

    script_name = "SoftwareInstance_checkInstanceTreeMonitoringState"
    with TemporaryAlarmScript(self.portal, script_name, attribute=None):
      alarm.activeSense()
      self.tic()
      content_a = instance_a.workflow_history['edit_workflow'][-1]['comment']
      content_b = instance_b.workflow_history['edit_workflow'][-1]['comment']

      # The alarm should group by project, so only one out of many should reached.
      self.assertNotEqual(content_a, content_b)
      self.assertIn('Visited by %s' % script_name, [content_a, content_b])

  @simulate('Project_isSupportRequestCreationClosed', '', 'return 0')
  @simulate('NotificationTool_getDocumentValue',
            'reference=None, **kw',
  'assert reference == "slapos-crm-instance-tree-instance-state.notification", reference\n' \
  'return context.restrictedTraverse(' \
  'context.REQUEST["test_SoftwareInstance_checkInstanceTreeMonitoringState_notify"])')
  def test_SoftwareInstance_checkInstanceTreeMonitoringState_script_notifyError(self):
    with PinnedDateTime(self, DateTime() - 1.1):
      project = self.addProject()
      self._makeComputeNode(project)
      self._makeComplexComputeNode(project)

      software_instance = self.start_requested_software_instance
      instance_tree = software_instance.getSpecialiseValue()
      software_instance.setErrorStatus("")

    self.portal.REQUEST['test_SoftwareInstance_checkInstanceTreeMonitoringState_notify'] = \
        self._makeNotificationMessage(instance_tree.getReference())
    self.tic()

    software_instance.SoftwareInstance_checkInstanceTreeMonitoringState()
    self.tic()

    ticket_title = "Instance Tree %s is failing." % (
      instance_tree.getTitle()
    )
    ticket = self._getGeneratedSupportRequest(instance_tree.getUid())

    self.assertNotEqual(ticket, None)
    self.assertEqual(ticket.getTitle(), ticket_title)

    event_list = ticket.getFollowUpRelatedValueList()
    self.assertEqual(len(event_list), 1)
    event = event_list[0]

    self.assertEqual(
      event.getTitle(),
      self.portal.restrictedTraverse(
        self.portal.REQUEST['test_SoftwareInstance_checkInstanceTreeMonitoringState_notify']
      ).getTitle()
    )
    self.assertIn(instance_tree.getReference(), event.getTextContent())
    self.assertEventTicket(event, ticket, instance_tree)

  @simulate('Project_isSupportRequestCreationClosed', '', 'return 0')
  def test_SoftwareInstance_checkInstanceTreeMonitoringState_script_notifyErrorTolerance(self):
    with PinnedDateTime(self, DateTime() - 1.1):
      project = self.addProject()
      self._makeComputeNode(project)
      self._makeComplexComputeNode(project)

      software_instance = self.start_requested_software_instance
      instance_tree = software_instance.getSpecialiseValue()

    # Error is issued, but it is too early to create a ticket
    software_instance.setErrorStatus("")
    software_instance.SoftwareInstance_checkInstanceTreeMonitoringState()
    error_dict = software_instance.SoftwareInstance_getReportedErrorDict(
      tolerance=30)
    self.tic()

    self.assertEqual(error_dict['should_notify'], None)
    ticket = self._getGeneratedSupportRequest(instance_tree.getUid())
    self.assertEqual(ticket, None)

    # if no tolerance, the notification will be created
    error_dict = software_instance.SoftwareInstance_getReportedErrorDict(
      tolerance=0)
    self.assertEqual(error_dict['should_notify'], True)

  @simulate('Project_isSupportRequestCreationClosed', '', 'return 0')
  @simulate('NotificationTool_getDocumentValue',
            'reference=None, **kw',
  'assert reference == "slapos-crm-instance-tree-instance-allocation.notification", reference\n' \
  'return context.restrictedTraverse(' \
  'context.REQUEST["test_SoftwareInstance_checkInstanceTreeMonitoringState_notify"])')
  def test_SoftwareInstance_checkInstanceTreeMonitoringState_script_notifyNotAllocated(self):
    with PinnedDateTime(self, DateTime() - 1.1):
      project = self.addProject()
      self._makeComputeNode(project)
      self._makeComplexComputeNode(project)

      software_instance = self.start_requested_software_instance
      instance_tree = software_instance.getSpecialiseValue()

    self.portal.REQUEST['test_SoftwareInstance_checkInstanceTreeMonitoringState_notify'] = \
        self._makeNotificationMessage(instance_tree.getReference())
    self.tic()

    software_instance.edit(aggregate=None)
    software_instance.SoftwareInstance_checkInstanceTreeMonitoringState()
    error_dict = software_instance.SoftwareInstance_getReportedErrorDict(tolerance=30)
    self.tic()

    ticket_title = "Instance Tree %s is failing." % (instance_tree.getTitle())
    self.assertEqual(error_dict['ticket_title'], ticket_title)
    ticket = self._getGeneratedSupportRequest(instance_tree.getUid())

    self.assertNotEqual(ticket, None)
    self.assertEqual(ticket.getTitle(), error_dict['ticket_title'])
    event_list = ticket.getFollowUpRelatedValueList()
    self.assertEqual(len(event_list), 1)
    event = event_list[0]

    self.assertEqual(
      event.getTitle(),
      self.portal.restrictedTraverse(
        self.portal.REQUEST['test_SoftwareInstance_checkInstanceTreeMonitoringState_notify']
      ).getTitle()
    )
    self.assertIn(instance_tree.getReference(), event.getTextContent())
    self.assertEventTicket(event, ticket, instance_tree)

  @simulate('Project_isSupportRequestCreationClosed', '', 'return 0')
  @simulate('NotificationTool_getDocumentValue',
            'reference=None, **kw',
  'assert reference == "slapos-crm-instance-tree-instance-on-close-computer.notification", reference\n' \
  'return context.restrictedTraverse(' \
  'context.REQUEST["test_SoftwareInstance_checkInstanceTreeMonitoringState_notify"])')
  def test_SoftwareInstance_checkInstanceTreeMonitoringState_script_close_forever(self):
    with PinnedDateTime(self, DateTime() - 1.1):
      project = self.addProject()
      self._makeComputeNode(project)
      self._makeComplexComputeNode(project)

      software_instance = self.start_requested_software_instance
      instance_tree = software_instance.getSpecialiseValue()
      self.compute_node.setAllocationScope('close/forever')
      self.tic()

    self.portal.REQUEST['test_SoftwareInstance_checkInstanceTreeMonitoringState_notify'] = \
        self._makeNotificationMessage(instance_tree.getReference())
    self.compute_node.setMonitorScope('enabled')
    self.tic()

    software_instance.SoftwareInstance_checkInstanceTreeMonitoringState()
    error_dict = software_instance.SoftwareInstance_getReportedErrorDict(tolerance=30)
    self.tic()

    ticket_title =  "Instance Tree %s is failing." % (instance_tree.getTitle())
    self.assertEqual(error_dict['ticket_title'], ticket_title)
    ticket = self._getGeneratedSupportRequest(instance_tree.getUid())

    self.assertNotEqual(ticket, None)
    self.assertEqual(ticket.getTitle(), error_dict['ticket_title'])
    event_list = ticket.getFollowUpRelatedValueList()
    self.assertEqual(len(event_list), 1)
    event = event_list[0]

    self.assertEqual(
      event.getTitle(),
      self.portal.restrictedTraverse(
        self.portal.REQUEST['test_SoftwareInstance_checkInstanceTreeMonitoringState_notify']
      ).getTitle()
    )
    self.assertIn(instance_tree.getReference(), event.getTextContent())
    self.assertEventTicket(event, ticket, instance_tree)

  @simulate('Project_isSupportRequestCreationClosed', '', 'return 0')
  def test_SoftwareInstance_checkInstanceTreeMonitoringState_script_tooEarly(self):
    with PinnedDateTime(self, DateTime()):
      project = self.addProject()
      self._makeComputeNode(project)
      self._makeComplexComputeNode(project)

      software_instance = self.start_requested_software_instance
      instance_tree = software_instance.getSpecialiseValue()
      software_instance.setErrorStatus("")

    self.tic()

    software_instance.SoftwareInstance_checkInstanceTreeMonitoringState()
    error_dict = software_instance.SoftwareInstance_getReportedErrorDict(
      tolerance=30)
    self.tic()

    ticket = self._getGeneratedSupportRequest(instance_tree.getUid())

    self.assertEqual(ticket, None)
    self.assertEqual(error_dict['should_notify'], None)

  @simulate('Project_isSupportRequestCreationClosed', '', 'return 1')
  def test_SoftwareInstance_checkInstanceTreeMonitoringState_script_closed(self):
    with PinnedDateTime(self, DateTime() - 1):
      project = self.addProject()
      self._makeComputeNode(project)
      self._makeComplexComputeNode(project)

      software_instance = self.start_requested_software_instance
      instance_tree = software_instance.getSpecialiseValue()
      software_instance.setErrorStatus("")

    self.tic()

    error_dict = software_instance.SoftwareInstance_getReportedErrorDict()
    software_instance.SoftwareInstance_checkInstanceTreeMonitoringState()
    self.tic()

    ticket = self._getGeneratedSupportRequest(instance_tree.getUid())
    self.assertEqual(ticket, None)
    self.assertEqual(error_dict['should_notify'], True)

  @simulate('Project_isSupportRequestCreationClosed', '', 'return 0')
  def test_SoftwareInstance_checkInstanceTreeMonitoringState_script_slaveInstance(self):
    with PinnedDateTime(self, DateTime() - 1.1):
      _, _, _, _, _, instance_tree = self.bootstrapAllocableInstanceTree(
        node='instance', allocation_state='allocated', shared=True)
      software_instance = instance_tree.getSuccessorValue()
      software_instance.setErrorStatus("foo")

    self.tic()

    error_dict = software_instance.SoftwareInstance_getReportedErrorDict()
    software_instance.SoftwareInstance_checkInstanceTreeMonitoringState()
    self.tic()

    ticket = self._getGeneratedSupportRequest(instance_tree.getUid())
    self.assertEqual(error_dict['should_notify'], True)

    ticket_title =  "Instance Tree %s is failing." % (instance_tree.getTitle())
    self.assertEqual(error_dict['ticket_title'], ticket_title)
    ticket = self._getGeneratedSupportRequest(instance_tree.getUid())

    self.assertNotEqual(ticket, None)
    self.assertEqual(ticket.getTitle(), error_dict['ticket_title'])
    event_list = ticket.getFollowUpRelatedValueList()
    self.assertEqual(len(event_list), 1)
    event = event_list[0]

    self.assertIn('#error foo', event.getTextContent())
    self.assertEventTicket(event, ticket, instance_tree)

  @simulate('Project_isSupportRequestCreationClosed', '', 'return 0')
  def test_SoftwareInstance_checkInstanceTreeMonitoringState_script_slaveWithoutSoftwareInstance(self):
    with PinnedDateTime(self, DateTime() - 1.1):
      # without instance='node', the slave is allocated w/o software instance
      # which emulates post unallocation state after the destruction of
      # the software instance.
      _, _, _, _, _, instance_tree = self.bootstrapAllocableInstanceTree(
        allocation_state='allocated', shared=True)
      software_instance = instance_tree.getSuccessorValue()
    self.tic()

    error_dict = software_instance.SoftwareInstance_getReportedErrorDict()
    software_instance.SoftwareInstance_checkInstanceTreeMonitoringState()
    self.tic()

    ticket = self._getGeneratedSupportRequest(instance_tree.getUid())
    self.assertEqual(error_dict['should_notify'], True)

    ticket_title =  "Instance Tree %s is failing." % (instance_tree.getTitle())
    self.assertEqual(error_dict['ticket_title'], ticket_title)
    ticket = self._getGeneratedSupportRequest(instance_tree.getUid())

    self.assertNotEqual(ticket, None)
    self.assertEqual(ticket.getTitle(), error_dict['ticket_title'])
    event_list = ticket.getFollowUpRelatedValueList()
    self.assertEqual(len(event_list), 1)
    event = event_list[0]

    self.assertIn('is allocated on a destroyed software instance',
                  event.getTextContent())
    self.assertEqual(event.getFollowUp(), ticket.getRelativeUrl())
    self.assertEventTicket(event, ticket, instance_tree)


  @simulate('Project_isSupportRequestCreationClosed', '', 'return 0')
  def test_SoftwareInstance_checkInstanceTreeMonitoringState_script_instanceBadComputeGuid(self):
    with PinnedDateTime(self, DateTime() - 1.1):
      project = self.addProject()
      self._makeComputeNode(project)
      self._makeComplexComputeNode(project)

    software_instance = self.start_requested_software_instance
    instance_tree = software_instance.getSpecialiseValue()

    # Something changed before allocation for whatever reason
    software_instance.setSlaXml("""<?xml version='1.0' encoding='utf-8'?>
        <instance>
        <parameter id='computer_guid'>%s_foo</parameter>
        </instance>""" % self.compute_node.getReference())

    instance_tree.setSlaXml(software_instance.getSlaXml())

    self.tic()

    software_instance.SoftwareInstance_checkInstanceTreeMonitoringState()
    error_dict = software_instance.SoftwareInstance_getReportedErrorDict(tolerance=30)
    self.tic()

    ticket_title = "Instance Tree %s is failing." % (instance_tree.getTitle())
    self.assertEqual(error_dict['ticket_title'], ticket_title)
    ticket = self._getGeneratedSupportRequest(instance_tree.getUid())

    self.assertNotEqual(ticket, None)
    self.assertEqual(ticket.getTitle(), error_dict['ticket_title'])
    event_list = ticket.getFollowUpRelatedValueList()
    self.assertEqual(len(event_list), 1)
    event = event_list[0]

    self.assertIn('has invalid Service Level Aggrement.',
                  event.getTextContent())
    self.assertIn(' computer_guid do not match on:',
                  event.getTextContent())
    self.assertEqual(event.getFollowUp(), ticket.getRelativeUrl())
    self.assertEventTicket(event, ticket, instance_tree)


  @simulate('Project_isSupportRequestCreationClosed', '', 'return 0')
  def test_SoftwareInstance_checkInstanceTreeMonitoringState_script_instanceBadNetworkGuid(self):
    with PinnedDateTime(self, DateTime() - 1.1):
      project = self.addProject()
      self._makeComputeNode(project)
      self._makeComplexComputeNode(project)

    software_instance = self.start_requested_software_instance
    instance_tree = software_instance.getSpecialiseValue()

    # Something changed before allocation for whatever reason
    software_instance.setSlaXml("""<?xml version='1.0' encoding='utf-8'?>
        <instance>
        <parameter id='network_guid'>NETFAKE-1</parameter>
        </instance>""")

    instance_tree.setSlaXml(software_instance.getSlaXml())

    self.tic()

    software_instance.SoftwareInstance_checkInstanceTreeMonitoringState()
    error_dict = software_instance.SoftwareInstance_getReportedErrorDict(tolerance=30)
    self.tic()

    ticket_title = "Instance Tree %s is failing." % (instance_tree.getTitle())
    self.assertEqual(error_dict['ticket_title'], ticket_title)
    ticket = self._getGeneratedSupportRequest(instance_tree.getUid())

    self.assertNotEqual(ticket, None)
    self.assertEqual(ticket.getTitle(), error_dict['ticket_title'])
    event_list = ticket.getFollowUpRelatedValueList()
    self.assertEqual(len(event_list), 1)
    event = event_list[0]

    self.assertIn('has invalid Service Level Aggrement.',
                  event.getTextContent())
    self.assertIn(' network_guid do not match on:',
                  event.getTextContent())
    self.assertEventTicket(event, ticket, instance_tree)


  @simulate('Project_isSupportRequestCreationClosed', '', 'return 0')
  def test_SoftwareInstance_checkInstanceTreeMonitoringState_script_instanceBadProjectGuid(self):
    with PinnedDateTime(self, DateTime() - 1.1):
      project = self.addProject()
      self._makeComputeNode(project)
      self._makeComplexComputeNode(project)

    software_instance = self.start_requested_software_instance
    instance_tree = software_instance.getSpecialiseValue()

    # Something changed before allocation for whatever reason
    software_instance.setSlaXml("""<?xml version='1.0' encoding='utf-8'?>
        <instance>
        <parameter id='project_guid'>PROJFAKE-1</parameter>
        </instance>""")

    instance_tree.setSlaXml(software_instance.getSlaXml())

    self.tic()

    software_instance.SoftwareInstance_checkInstanceTreeMonitoringState()
    error_dict = software_instance.SoftwareInstance_getReportedErrorDict(tolerance=30)
    self.tic()

    ticket_title = "Instance Tree %s is failing." % (instance_tree.getTitle())
    self.assertEqual(error_dict['ticket_title'], ticket_title)
    ticket = self._getGeneratedSupportRequest(instance_tree.getUid())

    self.assertNotEqual(ticket, None)
    self.assertEqual(ticket.getTitle(), error_dict['ticket_title'])
    event_list = ticket.getFollowUpRelatedValueList()
    self.assertEqual(len(event_list), 1)
    event = event_list[0]

    self.assertIn('has invalid Service Level Aggrement.',
                  event.getTextContent())
    self.assertIn(' project_guid do not match on:',
                  event.getTextContent())
    self.assertEventTicket(event, ticket, instance_tree)

  @simulate('Project_isSupportRequestCreationClosed', '', 'return 0')
  def test_SoftwareInstance_checkInstanceTreeMonitoringState_script_instanceWrongProject(self):
    with PinnedDateTime(self, DateTime() - 1.1):
      project = self.addProject()
      self._makeComputeNode(project)
      self._makeComplexComputeNode(project)

    software_instance = self.start_requested_software_instance
    instance_tree = software_instance.getSpecialiseValue()

    other_project = self.addProject()
    # Forcefully move node to some other project
    self.compute_node.setFollowUpValue(other_project)

    # Double check if the instance is properly allocated on where
    # we expect to be.
    self.assertEqual(self.compute_node.getRelativeUrl(),
      software_instance.getAggregateValue().getParentValue().getRelativeUrl())

    self.tic()

    software_instance.SoftwareInstance_checkInstanceTreeMonitoringState()
    error_dict = software_instance.SoftwareInstance_getReportedErrorDict(tolerance=30)
    self.tic()

    ticket_title = "Instance Tree %s is failing." % (instance_tree.getTitle())
    self.assertEqual(error_dict['ticket_title'], ticket_title)
    ticket = self._getGeneratedSupportRequest(instance_tree.getUid())

    self.assertNotEqual(ticket, None)
    self.assertEqual(ticket.getTitle(), error_dict['ticket_title'])
    event_list = ticket.getFollowUpRelatedValueList()
    self.assertEqual(len(event_list), 1)
    event = event_list[0]

    self.assertIn('has invalid Service Level Aggrement.',
                  event.getTextContent())
    self.assertIn(' Instance and Compute node project do not match on:',
                  event.getTextContent())
    self.assertEventTicket(event, ticket, instance_tree)

  @simulate('Project_isSupportRequestCreationClosed', '', 'return 0')
  def test_SoftwareInstance_checkInstanceTreeMonitoringState_script_instanceBadInstanceGuid(self):
    with PinnedDateTime(self, DateTime() - 1.1):
      project = self.addProject()
      self._makeComputeNode(project)
      self._makeComplexComputeNode(project)

    software_instance = self.start_requested_software_instance
    instance_tree = software_instance.getSpecialiseValue()

    # Something changed before allocation for whatever reason
    software_instance.setSlaXml("""<?xml version='1.0' encoding='utf-8'?>
        <instance>
        <parameter id='instance_guid'>SIFAKE-1</parameter>
        </instance>""")

    instance_tree.setSlaXml(software_instance.getSlaXml())

    self.tic()

    software_instance.SoftwareInstance_checkInstanceTreeMonitoringState()
    error_dict = software_instance.SoftwareInstance_getReportedErrorDict(tolerance=30)
    self.tic()

    ticket_title = "Instance Tree %s is failing." % (instance_tree.getTitle())
    self.assertEqual(error_dict['ticket_title'], ticket_title)
    ticket = self._getGeneratedSupportRequest(instance_tree.getUid())

    self.assertNotEqual(ticket, None)
    self.assertEqual(ticket.getTitle(), error_dict['ticket_title'])
    event_list = ticket.getFollowUpRelatedValueList()
    self.assertEqual(len(event_list), 1)
    event = event_list[0]

    self.assertIn('has invalid Service Level Aggrement.',
                  event.getTextContent())
    self.assertIn(' instance_guid is provided to a Software Instance:',
                  event.getTextContent())
    self.assertEventTicket(event, ticket, instance_tree)

  @simulate('Project_isSupportRequestCreationClosed', '', 'return 0')
  def test_SoftwareInstance_checkInstanceTreeMonitoringState_script_slaveInstanceGuidOnRemote(self):
    with PinnedDateTime(self, DateTime() - 1.1):
      _, _, _, _, _, instance_tree = self.bootstrapAllocableInstanceTree(
          allocation_state='allocated', node='remote', shared=True)
      software_instance = instance_tree.getSuccessorValue()

    # Something changed before allocation for whatever reason
    software_instance.setSlaXml("""<?xml version='1.0' encoding='utf-8'?>
        <instance>
        <parameter id='instance_guid'>SIFAKE-1</parameter>
        </instance>""")

    instance_tree.setSlaXml(software_instance.getSlaXml())

    self.tic()

    software_instance.SoftwareInstance_checkInstanceTreeMonitoringState()
    error_dict = software_instance.SoftwareInstance_getReportedErrorDict(tolerance=30)
    self.tic()

    # For now the assertion is disabled, so we do not generate a ticket for
    # this use case. Until allocation is improved to consider this a problem
    ticket = self._getGeneratedSupportRequest(instance_tree.getUid())
    self.assertEqual(ticket, None)
    self.assertEqual(error_dict['should_notify'], None)

    # Uncommend the following to when the SoftwareInstance_getReportedErrorDict
    # changes back.
    #ticket_title = "Instance Tree %s is failing." % (instance_tree.getTitle())
    #self.assertEqual(error_dict['ticket_title'], ticket_title)
    #ticket = self._getGeneratedSupportRequest(instance_tree.getUid())

    #self.assertNotEqual(ticket, None)
    #self.assertEqual(ticket.getTitle(), error_dict['ticket_title'])
    #event_list = ticket.getFollowUpRelatedValueList()
    #self.assertEqual(len(event_list), 1)
    #event = event_list[0]

    #self.assertIn('has invalid Service Level Aggrement.',
    #              event.getTextContent())
    #self.assertIn(
    #  ' instance_guid provided on test tree and it is allocated on a REMOTE NODE',
    #  event.getTextContent())
    #self.assertEventTicket(event, ticket, instance_tree)

  @simulate('Project_isSupportRequestCreationClosed', '', 'return 0')
  def test_SoftwareInstance_checkInstanceTreeMonitoringState_script_slaveBadInstanceGuid(self):
    with PinnedDateTime(self, DateTime() - 1.1):
      _, _, _, _, _, instance_tree = self.bootstrapAllocableInstanceTree(
        node='instance', allocation_state='allocated', shared=True)
      software_instance = instance_tree.getSuccessorValue()

    # Something changed before allocation for whatever reason
    software_instance.setSlaXml("""<?xml version='1.0' encoding='utf-8'?>
        <instance>
        <parameter id='instance_guid'>SIFAKE-1</parameter>
        </instance>""")

    self.tic()

    error_dict = software_instance.SoftwareInstance_getReportedErrorDict()
    software_instance.SoftwareInstance_checkInstanceTreeMonitoringState()
    self.tic()

    ticket = self._getGeneratedSupportRequest(instance_tree.getUid())
    self.assertEqual(error_dict['should_notify'], True)

    ticket_title =  "Instance Tree %s is failing." % (instance_tree.getTitle())
    self.assertEqual(error_dict['ticket_title'], ticket_title)
    ticket = self._getGeneratedSupportRequest(instance_tree.getUid())

    self.assertNotEqual(ticket, None)
    self.assertEqual(ticket.getTitle(), error_dict['ticket_title'])
    event_list = ticket.getFollowUpRelatedValueList()
    self.assertEqual(len(event_list), 1)
    event = event_list[0]

    self.assertIn(' instance_guid do not match on:', event.getTextContent())
    self.assertEventTicket(event, ticket, instance_tree)

  @simulate('Project_isSupportRequestCreationClosed', '', 'return 0')
  def test_SoftwareInstance_checkInstanceTreeMonitoringState_script_instanceOnRemoteNode(self):
    with PinnedDateTime(self, DateTime() - 1.1):
      _, _, _, _, _, instance_tree = self.bootstrapAllocableInstanceTree(allocation_state='allocated', node='remote')
      software_instance = instance_tree.getSuccessorValue()
      software_instance.setErrorStatus("foo2")

    self.tic()

    error_dict = software_instance.SoftwareInstance_getReportedErrorDict()
    software_instance.SoftwareInstance_checkInstanceTreeMonitoringState()
    self.tic()

    ticket = self._getGeneratedSupportRequest(instance_tree.getUid())
    self.assertEqual(error_dict['should_notify'], True)

    ticket_title =  "Instance Tree %s is failing." % (instance_tree.getTitle())
    self.assertEqual(error_dict['ticket_title'], ticket_title)
    ticket = self._getGeneratedSupportRequest(instance_tree.getUid())

    self.assertNotEqual(ticket, None)
    self.assertEqual(ticket.getTitle(), error_dict['ticket_title'])
    event_list = ticket.getFollowUpRelatedValueList()
    self.assertEqual(len(event_list), 1)
    event = event_list[0]

    self.assertIn('#error foo2', event.getTextContent())
    self.assertEventTicket(event, ticket, instance_tree)

class TestSlaposCrmUpdateSupportRequestState(TestSlapOSCrmMonitoringMixin):

  def _makeInstanceTree(self):
    person = self.portal.person_module\
         .newContent(portal_type="Person")
    instance_tree = self.portal\
      .instance_tree_module\
      .newContent(portal_type="Instance Tree")
    instance_tree.validate()
    new_id = self.generateNewId()
    instance_tree.edit(
        title= "Test hosting sub ticket %s" % new_id,
        reference="TESTHST-%s" % new_id,
        destination_section_value=person,
        monitor_scope="enabled"
    )

    return instance_tree

  def test_SupportRequest_updateMonitoringState_alarm_monitoring(self):
    support_request = self._makeSupportRequest()
    support_request.setResource("service_module/slapos_crm_monitoring")
    hs = self._makeInstanceTree()
    support_request.setCausalityValue(hs)
    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_update_support_request_state
    self._test_alarm(alarm, support_request, "SupportRequest_updateMonitoringState")

  def test_SupportRequest_updateMonitoringState_alarm_notResource(self):
    support_request = self._makeSupportRequest()
    hs = self._makeInstanceTree()
    support_request.setAggregateValue(hs)
    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_update_support_request_state
    self._test_alarm_not_visited(alarm, support_request, "SupportRequest_updateMonitoringState")

  def test_SupportRequest_updateMonitoringState_alarm_notValidated(self):
    support_request = self._makeSupportRequest()
    support_request.setResource("service_module/slapos_crm_monitoring")
    support_request.validate()
    support_request.invalidate()
    hs = self._makeInstanceTree()
    support_request.setAggregateValue(hs)
    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_update_support_request_state
    self._test_alarm_not_visited(alarm, support_request,
                                 "SupportRequest_updateMonitoringState")

  def test_SupportRequest_updateMonitoringState_alarm_noInstanceTree(self):
    support_request = self._makeSupportRequest()
    support_request.setResource("service_module/slapos_crm_monitoring")
    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_update_support_request_state
    self._test_alarm_not_visited(alarm, support_request,
                                 "SupportRequest_updateMonitoringState")

  def _makeNotificationMessage(self, reference):
    notification_message = self.portal.notification_message_module.newContent(
      portal_type="Notification Message",
      title='Closing Support Request %s' % reference,
      text_content='Test NM content<br/>%s<br/>' % reference,
      content_type='text/html',
      )
    return notification_message.getRelativeUrl()

  @simulate('Project_isSupportRequestCreationClosed', '', 'return 0')
  @simulate('NotificationTool_getDocumentValue',
            'reference=None, **kw',
  'assert reference == "slapos-crm-support-request-close-destroyed-notification", reference\n' \
  'return context.restrictedTraverse(' \
  'context.REQUEST["test_SupportRequest_updateMonitoringState_notify"])')
  def test_SupportRequest_updateMonitoringState_script_notifyClose(self):
    support_request = self._makeSupportRequest()
    support_request.setResource("service_module/slapos_crm_monitoring")
    instance_tree = self._makeInstanceTree()
    support_request.setCausalityValue(instance_tree)
    self.tic()

    self.portal.REQUEST['test_SupportRequest_updateMonitoringState_notify'] = \
        self._makeNotificationMessage(instance_tree.getReference())
    self.tic()

    self.portal.portal_workflow._jumpToStateFor(instance_tree, "destroy_requested")
    support_request.SupportRequest_updateMonitoringState()
    self.tic()

    ticket = support_request

    event_list = ticket.getFollowUpRelatedValueList()
    self.assertEqual(len(event_list), 1)
    event = event_list[0]

    self.assertEqual(
      event.getTitle(),
      self.portal.restrictedTraverse(
        self.portal.REQUEST['test_SupportRequest_updateMonitoringState_notify']
      ).getTitle()
    )
    self.assertIn(instance_tree.getReference(), event.getTextContent())
    self.assertEqual(event.getFollowUp(), ticket.getRelativeUrl())
    self.assertEqual(event.getSourceProject(), instance_tree.getFollowUp())
    self.assertEqual(ticket.getSourceProject(), instance_tree.getFollowUp())
    self.assertEqual(ticket.getCausality(), instance_tree.getRelativeUrl())
    self.assertEqual(ticket.getSimulationState(), "invalidated")
    self.assertEqual(event.getSimulationState(), "delivered")
    self.assertEqual(event.getPortalType(), "Web Message")

  @simulate('Project_isSupportRequestCreationClosed', '', 'return 0')
  def test_SupportRequest_updateMonitoringState_script_notDestroyed(self):
    support_request = self._makeSupportRequest()
    support_request.setResource("service_module/slapos_crm_monitoring")
    instance_tree = self._makeInstanceTree()
    support_request.setCausalityValue(instance_tree)
    self.tic()

    self.portal.REQUEST['test_SupportRequest_updateMonitoringState_notify'] = \
        self._makeNotificationMessage(instance_tree.getReference())
    self.tic()

    self.assertEqual(support_request.getSimulationState(), "submitted")
    support_request.SupportRequest_updateMonitoringState()
    self.tic()

    ticket = support_request

    event_list = ticket.getFollowUpRelatedValueList()
    self.assertEqual(len(event_list), 0)
    self.assertEqual(ticket.getSimulationState(), "submitted")

  @simulate('Project_isSupportRequestCreationClosed', '', 'return 0')
  def test_SupportRequest_updateMonitoringState_script_invalidated(self):
    support_request = self._makeSupportRequest()
    support_request.setResource("service_module/slapos_crm_monitoring")
    instance_tree = self._makeInstanceTree()
    support_request.setCausalityValue(instance_tree)
    self.tic()

    self.portal.REQUEST['test_SupportRequest_updateMonitoringState_notify'] = \
        self._makeNotificationMessage(instance_tree.getReference())
    self.tic()

    support_request.validate()
    support_request.invalidate()
    support_request.SupportRequest_updateMonitoringState()
    self.tic()

    ticket = support_request

    event_list = ticket.getFollowUpRelatedValueList()
    self.assertEqual(len(event_list), 0)
    self.assertEqual(ticket.getSimulationState(), "invalidated")


class TestSlaposCrmCheckStoppedEventToDeliver(TestSlapOSCrmMonitoringMixin):

  def _makeEvent(self, ticket):
    new_id = self.generateNewId()
    return self.portal.event_module.newContent(
      portal_type="Web Message",
      title='Test Event %s' % new_id,
      follow_up_value=ticket
    )

  def test_Event_checkStoppedEventFromSupportRequestToDeliver_alarm_stopped(self):
    support_request = self._makeSupportRequest()
    event = self._makeEvent(support_request)
    event.stop()
    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm', "'disabled'", attribute='comment'):
      self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_check_stopped_event_from_support_request_to_deliver
    self._test_alarm(alarm, event, "Event_checkStoppedFromSupportRequestToDeliver")

  def test_Event_checkStoppedEventFromSupportRequestToDeliver_alarm_delivered(self):
    support_request = self._makeSupportRequest()
    event = self._makeEvent(support_request)
    event.stop()
    event.deliver()
    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm', "'disabled'", attribute='comment'):
      self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_check_stopped_event_from_support_request_to_deliver
    self._test_alarm_not_visited(alarm, event, "Event_checkStoppedFromSupportRequestToDeliver")

  def test_Event_checkStoppedEventFromSupportRequestToDeliver_alarm_stoppedWithoutTicket(self):
    support_request = self._makeSupportRequest()
    event = self._makeEvent(support_request)
    event.setFollowUp(None)
    event.stop()
    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm', "'disabled'", attribute='comment'):
      self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_check_stopped_event_from_support_request_to_deliver
    self._test_alarm_not_visited(alarm, event, "Event_checkStoppedFromSupportRequestToDeliver")

  def test_Event_checkStoppedEventFromSupportRequestToDeliver_script_recentEventInvalidatedTicket(self):
    support_request = self._makeSupportRequest()
    support_request.validate()
    support_request.invalidate()
    self.tic()
    time.sleep(1)
    event = self._makeEvent(support_request)
    event.stop()
    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm', "'disabled'", attribute='comment'):
      self.tic()
    self.assertEqual(event.getSimulationState(), "stopped")
    self.assertEqual(support_request.getSimulationState(), "invalidated")
    event.Event_checkStoppedFromSupportRequestToDeliver()
    self.assertEqual(event.getSimulationState(), "delivered")
    self.assertEqual(support_request.getSimulationState(), "validated")

  def test_Event_checkStoppedEventFromSupportRequestToDeliver_script_recentEventValidatedTicket(self):
    support_request = self._makeSupportRequest()
    support_request.validate()
    self.tic()
    time.sleep(1)
    event = self._makeEvent(support_request)
    event.stop()
    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm', "'disabled'", attribute='comment'):
      self.tic()
    self.assertEqual(event.getSimulationState(), "stopped")
    self.assertEqual(support_request.getSimulationState(), "validated")
    event.Event_checkStoppedFromSupportRequestToDeliver()
    self.assertEqual(event.getSimulationState(), "delivered")
    self.assertTrue(event.getCreationDate() < support_request.getModificationDate())

  def test_Event_checkStoppedEventFromSupportRequestToDeliver_script_recentEventSuspendedTicket(self):
    support_request = self._makeSupportRequest()
    support_request.validate()
    support_request.suspend()
    self.tic()
    time.sleep(1)
    event = self._makeEvent(support_request)
    event.stop()
    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm', "'disabled'", attribute='comment'):
      self.tic()
    self.assertEqual(event.getSimulationState(), "stopped")
    self.assertEqual(support_request.getSimulationState(), "suspended")
    event.Event_checkStoppedFromSupportRequestToDeliver()
    self.assertEqual(event.getSimulationState(), "stopped")
    self.assertEqual(support_request.getSimulationState(), "suspended")

  def test_Event_checkStoppedEventFromSupportRequestToDeliver_script_oldEventInvalidatedTicket(self):
    support_request = self._makeSupportRequest()
    event = self._makeEvent(support_request)
    event.stop()
    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm', "'disabled'", attribute='comment'):
      self.tic()
    time.sleep(1)
    support_request.validate()
    support_request.invalidate()
    self.tic()
    self.assertEqual(event.getSimulationState(), "stopped")
    self.assertEqual(support_request.getSimulationState(), "invalidated")
    event.Event_checkStoppedFromSupportRequestToDeliver()
    self.assertEqual(event.getSimulationState(), "delivered")
    self.assertEqual(support_request.getSimulationState(), "invalidated")

  def test_Event_checkStoppedEventFromSupportRequestToDeliver_script_oldEventValidatedTicket(self):
    support_request = self._makeSupportRequest()
    event = self._makeEvent(support_request)
    event.stop()
    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm', "'disabled'", attribute='comment'):
      self.tic()
    time.sleep(1)
    support_request.validate()
    self.tic()
    self.assertEqual(event.getSimulationState(), "stopped")
    self.assertEqual(support_request.getSimulationState(), "validated")
    event.Event_checkStoppedFromSupportRequestToDeliver()
    self.assertEqual(event.getSimulationState(), "delivered")
    self.assertEqual(support_request.getSimulationState(), "validated")

  def test_Event_checkStoppedEventFromSupportRequestToDeliver_script_oldEventSuspendedTicket(self):
    support_request = self._makeSupportRequest()
    event = self._makeEvent(support_request)
    event.stop()
    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm', "'disabled'", attribute='comment'):
      self.tic()
    time.sleep(1)
    support_request.validate()
    support_request.suspend()
    self.tic()
    self.assertEqual(event.getSimulationState(), "stopped")
    self.assertEqual(support_request.getSimulationState(), "suspended")
    event.Event_checkStoppedFromSupportRequestToDeliver()
    self.assertEqual(event.getSimulationState(), "stopped")
    self.assertEqual(support_request.getSimulationState(), "suspended")


class TestSlaposCrmCheckSuspendedSupportRequestToReopen(TestSlapOSCrmMonitoringMixin):

  def test_SupportRequest_checkSuspendedSupportRequestToReopen_alarm_suspended(self):
    support_request = self._makeSupportRequest()
    support_request.validate()
    support_request.suspend()
    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_check_suspended_support_request_to_reopen
    self._test_alarm(alarm, support_request, "SupportRequest_checkSuspendedToReopen")

  def test_SupportRequest_checkSuspendedSupportRequestToReopen_alarm_notSuspended(self):
    support_request = self._makeSupportRequest()
    support_request.validate()
    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_check_suspended_support_request_to_reopen
    self._test_alarm_not_visited(alarm, support_request, "SupportRequest_checkSuspendedToReopen")

  def _makeEvent(self, ticket):
    new_id = self.generateNewId()
    return self.portal.event_module.newContent(
      portal_type="Web Message",
      title='Test Event %s' % new_id,
      follow_up_value=ticket
    )

  def test_SupportRequest_checkSuspendedSupportRequestToReopen_script_noEvent(self):
    support_request = self._makeSupportRequest()
    support_request.validate()
    support_request.suspend()
    self.tic()
    support_request.SupportRequest_checkSuspendedToReopen()
    self.assertEqual(support_request.getSimulationState(), "suspended")

  def test_SupportRequest_checkSuspendedSupportRequestToReopen_script_recentEvent(self):
    support_request = self._makeSupportRequest()
    support_request.validate()
    support_request.suspend()
    self.tic()
    time.sleep(1)
    self._makeEvent(support_request)
    self.tic()
    support_request.SupportRequest_checkSuspendedToReopen()
    self.assertEqual(support_request.getSimulationState(), "validated")

  def test_SupportRequest_checkSuspendedSupportRequestToReopen_script_oldEvent(self):
    support_request = self._makeSupportRequest()
    self._makeEvent(support_request)
    self.tic()
    time.sleep(1)
    support_request.validate()
    support_request.suspend()
    self.tic()
    support_request.SupportRequest_checkSuspendedToReopen()
    self.assertEqual(support_request.getSimulationState(), "suspended")

