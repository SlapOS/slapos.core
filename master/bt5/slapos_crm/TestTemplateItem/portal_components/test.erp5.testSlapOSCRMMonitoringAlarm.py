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


class TestSlapOSCrmMonitoringCheckComputeNodeProjectState(TestSlapOSCrmMonitoringMixin):
  launch_caucase = 1

  ##########################################################################
  # slapos_crm_monitoring_project > ComputeNode_checkMonitoringState
  ##########################################################################
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
      self.assertSameSet(['Visited by %s' % script_name, None], [content_a, content_b])


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
    self.assertEqual(event.getFollowUp(), ticket.getRelativeUrl())
    self.assertEqual(event.getSourceProject(), compute_node.getFollowUp())
    self.assertEqual(ticket.getSourceProject(), compute_node.getFollowUp())
    self.assertEqual(ticket.getCausality(), compute_node.getRelativeUrl())
    self.assertEqual(ticket.getSimulationState(), "submitted")
    self.assertEqual(event.getSimulationState(), "delivered")
    self.assertEqual(event.getPortalType(), "Web Message")

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
        self.portal.REQUEST['test_ComputeNode_checkMonitoringState_empty_cache_notify']
      ).getTitle()
    )
    self.assertIn(compute_node.getReference(), event.getTextContent())
    self.assertEqual(event.getFollowUp(), ticket.getRelativeUrl())
    self.assertEqual(event.getSourceProject(), compute_node.getFollowUp())
    self.assertEqual(ticket.getSourceProject(), compute_node.getFollowUp())
    self.assertEqual(ticket.getCausality(), compute_node.getRelativeUrl())
    self.assertEqual(ticket.getSimulationState(), "submitted")
    self.assertEqual(event.getSimulationState(), "delivered")
    self.assertEqual(event.getPortalType(), "Web Message")

  @simulate('Project_isSupportRequestCreationClosed', '*args, **kwargs', 'return 0')
  @simulate('NotificationTool_getDocumentValue',
            'reference=None, **kw',
  'assert reference == "slapos-crm-compute_node_check_stalled_instance_state.notification", reference\n' \
  'return context.restrictedTraverse(' \
  'context.REQUEST["test_ComputeNode_checkMonitoringState_stalled_instance"])')
  def test_ComputeNode_checkMonitoringState_script_stalledInstance(self):
    compute_node, _ = self._makeComputeNode(self.addProject())
    self._makeComplexComputeNode(self.addProject())
    compute_node = self.compute_node

    self.portal.REQUEST['test_ComputeNode_checkMonitoringState_stalled_instance'] = \
        self._makeNotificationMessage(compute_node.getReference())

    # Computer is getting access
    compute_node.setAccessStatus("")

    with PinnedDateTime(self, DateTime() - 1.1):
      self.start_requested_software_instance.setAccessStatus("")

    compute_node.ComputeNode_checkMonitoringState()
    self.tic()

    ticket_title = "Compute Node %s has a stalled instance process" % compute_node.getReference()
    ticket = self._getGeneratedSupportRequest(compute_node.getUid())
    self.assertNotEqual(ticket, None)
    self.assertEqual(ticket.getTitle(), ticket_title)

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
    self.assertEqual(event.getFollowUp(), ticket.getRelativeUrl())
    self.assertEqual(event.getSourceProject(), compute_node.getFollowUp())
    self.assertEqual(ticket.getSourceProject(), compute_node.getFollowUp())
    self.assertEqual(ticket.getCausality(), compute_node.getRelativeUrl())
    self.assertEqual(ticket.getSimulationState(), "submitted")
    self.assertEqual(event.getSimulationState(), "delivered")
    self.assertEqual(event.getPortalType(), "Web Message")

  @simulate('Project_isSupportRequestCreationClosed', '*args, **kwargs', 'return 0')
  @simulate('NotificationTool_getDocumentValue',
            'reference=None, **kw',
  'assert reference == "slapos-crm-compute_node_check_stalled_instance_state.notification", reference\n' \
  'return context.restrictedTraverse(' \
  'context.REQUEST["test_ComputeNode_checkMonitoringState_stalled_instance"])')
  def test_ComputeNode_checkMonitoringState_script_stalledInstanceSingle(self):
    compute_node, _ = self._makeComputeNode(self.addProject())
    self._makeComplexComputeNode(self.addProject())
    compute_node = self.compute_node

    self.portal.REQUEST['test_ComputeNode_checkMonitoringState_stalled_instance'] = \
        self._makeNotificationMessage(compute_node.getReference())

    # Computer is getting access
    compute_node.setAccessStatus("")

    with PinnedDateTime(self, DateTime() - 1.1):
      self.start_requested_software_instance.setAccessStatus("")
      self.start_requested_software_installation.setAccessStatus("")

    compute_node.ComputeNode_checkMonitoringState()
    self.tic()

    ticket_title = "Compute Node %s has a stalled instance process" % compute_node.getReference()
    ticket = self._getGeneratedSupportRequest(compute_node.getUid())
    self.assertNotEqual(ticket, None)
    self.assertEqual(ticket.getTitle(), ticket_title)

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
    self.assertEqual(event.getFollowUp(), ticket.getRelativeUrl())
    self.assertEqual(event.getSourceProject(), compute_node.getFollowUp())
    self.assertEqual(ticket.getSourceProject(), compute_node.getFollowUp())
    self.assertEqual(ticket.getCausality(), compute_node.getRelativeUrl())
    self.assertEqual(ticket.getSimulationState(), "submitted")
    self.assertEqual(event.getSimulationState(), "delivered")
    self.assertEqual(event.getPortalType(), "Web Message")

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
    compute_node, _ = self._makeComputeNode(self.addProject())
    self._makeComplexComputeNode(self.addProject())
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
    compute_node.ComputeNode_checkMonitoringState()
    self.tic()

    ticket_title = "Compute Node %s has modified file" % compute_node.getReference()
    ticket = self._getGeneratedSupportRequest(compute_node.getUid())
    self.assertNotEqual(ticket, None)
    self.assertEqual(ticket.getTitle(), ticket_title)

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
    self.assertEqual(event.getFollowUp(), ticket.getRelativeUrl())
    self.assertEqual(event.getSourceProject(), compute_node.getFollowUp())
    self.assertEqual(ticket.getSourceProject(), compute_node.getFollowUp())
    self.assertEqual(ticket.getCausality(), compute_node.getRelativeUrl())
    self.assertEqual(ticket.getSimulationState(), "submitted")
    self.assertEqual(event.getSimulationState(), "delivered")
    self.assertEqual(event.getPortalType(), "Web Message")

  @simulate('Project_isSupportRequestCreationClosed', '*args, **kwargs', 'return 0')
  def test_ComputeNode_checkMonitoringState_installation_no_information(self):
    with PinnedDateTime(self, DateTime() - 1.1):
      compute_node, _ = self._makeComputeNode(self.addProject())
      self._makeComplexComputeNode(self.addProject())
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
      compute_node, _ = self._makeComputeNode(self.addProject())
      self._makeComplexComputeNode(self.addProject())
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
    compute_node, _ = self._makeComputeNode(self.addProject())
    self._makeComplexComputeNode(self.addProject())
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
      compute_node, _ = self._makeComputeNode(self.addProject())
      self._makeComplexComputeNode(self.addProject())
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

    self.assertEqual(ticket_title, error_dict['ticket_title'])
    self.assertEqual(ticket_title, ticket.getTitle())
    self.assertNotEqual(ticket, None)
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
    self.assertEqual(event.getFollowUp(), ticket.getRelativeUrl())
    self.assertEqual(event.getSourceProject(), compute_node.getFollowUp())
    self.assertEqual(ticket.getSourceProject(), compute_node.getFollowUp())
    self.assertEqual(ticket.getCausality(), compute_node.getRelativeUrl())
    self.assertEqual(ticket.getSimulationState(), "submitted")
    self.assertEqual(event.getSimulationState(), "delivered")
    self.assertEqual(event.getPortalType(), "Web Message")

  @simulate('Project_isSupportRequestCreationClosed', '*args, **kwargs', 'return 0')
  @simulate('NotificationTool_getDocumentValue',
            'reference=None, **kw',
  'assert reference == "slapos-crm-compute_node_software_installation_state.notification", reference\n' \
  'return context.restrictedTraverse(' \
  'context.REQUEST["test_ComputeNode_checkMonitoringState_notify"])')
  def test_ComputeNode_checkMonitoringState_installation_notifyError(self):
    with PinnedDateTime(self, DateTime() - 1.1):
      compute_node, _ = self._makeComputeNode(self.addProject())
      self._makeComplexComputeNode(self.addProject())
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

    self.assertNotEqual(ticket, None, error_dict)
    self.assertEqual(error_dict['ticket_title'], ticket_title)
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
    self.assertEqual(event.getFollowUp(), ticket.getRelativeUrl())
    self.assertEqual(event.getSourceProject(), compute_node.getFollowUp())
    self.assertEqual(ticket.getSourceProject(), compute_node.getFollowUp())
    self.assertEqual(ticket.getCausality(), compute_node.getRelativeUrl())
    self.assertEqual(ticket.getSimulationState(), "submitted")
    self.assertEqual(event.getSimulationState(), "delivered")
    self.assertEqual(event.getPortalType(), "Web Message")


class TestSlapOSCrmSoftwareInstance_checkInstanceTreeMonitoringState(TestSlapOSCrmMonitoringMixin):
  launch_caucase = 1

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
      self.assertNotEquals(content_a, content_b)
      self.assertIn('Visited by %s' % script_name, [content_a, content_b])

  @simulate('Project_isSupportRequestCreationClosed', '', 'return 0')
  @simulate('NotificationTool_getDocumentValue',
            'reference=None, **kw',
  'assert reference == "slapos-crm-instance-tree-instance-state.notification", reference\n' \
  'return context.restrictedTraverse(' \
  'context.REQUEST["test_SoftwareInstance_checkInstanceTreeMonitoringState_notify"])')
  def test_SoftwareInstance_checkInstanceTreeMonitoringState_script_notifyError(self):
    with PinnedDateTime(self, DateTime() - 1.1):
      self._makeComputeNode(self.addProject())
      self._makeComplexComputeNode(self.addProject())

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
    self.assertEqual(event.getFollowUp(), ticket.getRelativeUrl())
    self.assertEqual(event.getSourceProject(), instance_tree.getFollowUp())
    self.assertEqual(ticket.getSourceProject(), instance_tree.getFollowUp())
    self.assertEqual(ticket.getCausality(), instance_tree.getRelativeUrl())
    self.assertEqual(ticket.getSimulationState(), "submitted")
    self.assertEqual(event.getSimulationState(), "delivered")
    self.assertEqual(event.getPortalType(), "Web Message")

  @simulate('Project_isSupportRequestCreationClosed', '', 'return 0')
  def test_SoftwareInstance_checkInstanceTreeMonitoringState_script_notifyErrorTolerance(self):
    with PinnedDateTime(self, DateTime() - 1.1):
      self._makeComputeNode(self.addProject())
      self._makeComplexComputeNode(self.addProject())

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
      self._makeComputeNode(self.addProject())
      self._makeComplexComputeNode(self.addProject())

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
    self.assertEqual(event.getFollowUp(), ticket.getRelativeUrl())
    self.assertEqual(event.getSourceProject(), instance_tree.getFollowUp())
    self.assertEqual(ticket.getSourceProject(), instance_tree.getFollowUp())
    self.assertEqual(ticket.getCausality(), instance_tree.getRelativeUrl())
    self.assertEqual(ticket.getSimulationState(), "submitted")
    self.assertEqual(event.getSimulationState(), "delivered")
    self.assertEqual(event.getPortalType(), "Web Message")


  @simulate('Project_isSupportRequestCreationClosed', '', 'return 0')
  @simulate('NotificationTool_getDocumentValue',
            'reference=None, **kw',
  'assert reference == "slapos-crm-instance-tree-instance-on-close-computer.notification", reference\n' \
  'return context.restrictedTraverse(' \
  'context.REQUEST["test_SoftwareInstance_checkInstanceTreeMonitoringState_notify"])')
  def test_SoftwareInstance_checkInstanceTreeMonitoringState_script_close_forever(self):
    with PinnedDateTime(self, DateTime() - 1.1):
      self._makeComputeNode(self.addProject())
      self._makeComplexComputeNode(self.addProject())

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
    self.assertEqual(event.getFollowUp(), ticket.getRelativeUrl())
    self.assertEqual(event.getSourceProject(), instance_tree.getFollowUp())
    self.assertEqual(ticket.getSourceProject(), instance_tree.getFollowUp())
    self.assertEqual(ticket.getCausality(), instance_tree.getRelativeUrl())
    self.assertEqual(ticket.getSimulationState(), "submitted")
    self.assertEqual(event.getSimulationState(), "delivered")
    self.assertEqual(event.getPortalType(), "Web Message")


  @simulate('Project_isSupportRequestCreationClosed', '', 'return 0')
  def test_SoftwareInstance_checkInstanceTreeMonitoringState_script_tooEarly(self):
    with PinnedDateTime(self, DateTime()):
      self._makeComputeNode(self.addProject())
      self._makeComplexComputeNode(self.addProject())

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
      self._makeComputeNode(self.addProject())
      self._makeComplexComputeNode(self.addProject())

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


class TestSlaposCrmUpdateSupportRequestState(SlapOSTestCaseMixinWithAbort):

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


class TestSlaposCrmCheckStoppedEventToDeliver(SlapOSTestCaseMixinWithAbort):

  def _makeSupportRequest(self):
    support_request = self.portal.support_request_module.newContent(
      portal_type="Support Request"
    )
    support_request.submit()
    new_id = self.generateNewId()
    support_request.edit(
        title= "Support Request éçà %s" % new_id, #pylint: disable=invalid-encoded-data
        reference="TESTSRQ-%s" % new_id
    )
    return support_request

  def _makeEvent(self, ticket):
    new_id = self.generateNewId()
    return self.portal.event_module.newContent(
      portal_type="Web Message",
      title='Test Event %s' % new_id,
      follow_up_value=ticket
    )

  def test_Event_checkStoppedEventToDeliver_alarm_stopped(self):
    support_request = self._makeSupportRequest()
    event = self._makeEvent(support_request)
    event.stop()
    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm', "'disabled'", attribute='comment'):
      self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_check_stopped_event_to_deliver
    self._test_alarm(alarm, event, "Event_checkStoppedToDeliver")

  def test_Event_checkStoppedEventToDeliver_alarm_delivered(self):
    support_request = self._makeSupportRequest()
    event = self._makeEvent(support_request)
    event.stop()
    event.deliver()
    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm', "'disabled'", attribute='comment'):
      self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_check_stopped_event_to_deliver
    self._test_alarm_not_visited(alarm, event, "Event_checkStoppedToDeliver")

  def test_Event_checkStoppedEventToDeliver_alarm_stoppedWithoutTicket(self):
    support_request = self._makeSupportRequest()
    event = self._makeEvent(support_request)
    event.setFollowUp(None)
    event.stop()
    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm', "'disabled'", attribute='comment'):
      self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_check_stopped_event_to_deliver
    self._test_alarm_not_visited(alarm, event, "Event_checkStoppedToDeliver")

  def test_Event_checkStoppedEventToDeliver_script_recentEventInvalidatedTicket(self):
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
    event.Event_checkStoppedToDeliver()
    self.assertEqual(event.getSimulationState(), "delivered")
    self.assertEqual(support_request.getSimulationState(), "validated")

  def test_Event_checkStoppedEventToDeliver_script_recentEventValidatedTicket(self):
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
    event.Event_checkStoppedToDeliver()
    self.assertEqual(event.getSimulationState(), "delivered")
    self.assertTrue(event.getCreationDate() < support_request.getModificationDate())

  def test_Event_checkStoppedEventToDeliver_script_recentEventSuspendedTicket(self):
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
    event.Event_checkStoppedToDeliver()
    self.assertEqual(event.getSimulationState(), "stopped")
    self.assertEqual(support_request.getSimulationState(), "suspended")

  def test_Event_checkStoppedEventToDeliver_script_oldEventInvalidatedTicket(self):
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
    event.Event_checkStoppedToDeliver()
    self.assertEqual(event.getSimulationState(), "delivered")
    self.assertEqual(support_request.getSimulationState(), "invalidated")

  def test_Event_checkStoppedEventToDeliver_script_oldEventValidatedTicket(self):
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
    event.Event_checkStoppedToDeliver()
    self.assertEqual(event.getSimulationState(), "delivered")
    self.assertEqual(support_request.getSimulationState(), "validated")

  def test_Event_checkStoppedEventToDeliver_script_oldEventSuspendedTicket(self):
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
    event.Event_checkStoppedToDeliver()
    self.assertEqual(event.getSimulationState(), "stopped")
    self.assertEqual(support_request.getSimulationState(), "suspended")


class TestSlaposCrmCheckSuspendedSupportRequestToReopen(SlapOSTestCaseMixinWithAbort):

  def _makeSupportRequest(self):
    support_request = self.portal.support_request_module.newContent(
      portal_type="Support Request"
    )
    support_request.submit()
    new_id = self.generateNewId()
    support_request.edit(
        title= "Support Request éçà %s" % new_id, #pylint: disable=invalid-encoded-data
        reference="TESTSRQ-%s" % new_id
    )

    return support_request

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

