# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (C) 2013-2019  Nexedi SA and Contributors.
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

import transaction
from erp5.component.test.SlapOSTestCaseMixin import \
  SlapOSTestCaseMixin,SlapOSTestCaseMixinWithAbort, simulate
from DateTime import DateTime
from App.Common import rfc1123_date
from Products.ERP5Type.Cache import DEFAULT_CACHE_SCOPE
import json

def getFakeSlapState():
  return "destroy_requested"

class TestCRMSkinsMixin(SlapOSTestCaseMixinWithAbort):

  def afterSetUp(self):
    SlapOSTestCaseMixinWithAbort.afterSetUp(self)
    self.person = self.makePerson(new_id=self.new_id, index=0, user=0)

  def _cancelTestSupportRequestList(self, title="%"):
    for support_request in self.portal.portal_catalog(
                        portal_type="Support Request",
                        title=title,
                        simulation_state=["validated", "suspended"]):
      support_request.invalidate()
    self.tic()

  def _updatePersonAssignment(self, person, role='role/member'):
    for assignment in person.contentValues(portal_type="Assignment"):
      assignment.cancel()
    assignment = person.newContent(portal_type='Assignment')
    assignment.setRole(role)
    assignment.setStartDate(DateTime())
    assignment.open()
    return assignment

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
        destination_section_value=person
    )

    return instance_tree

  def _makeSoftwareInstance(self, instance_tree, software_url):

    kw = dict(
      software_release=software_url,
      software_type=self.generateNewSoftwareType(),
      instance_xml=self.generateSafeXml(),
      sla_xml=self.generateSafeXml(),
      shared=False,
      software_title=instance_tree.getTitle(),
      state='started'
    )
    instance_tree.requestStart(**kw)
    instance_tree.requestInstance(**kw)


  def _makeSoftwareInstallation(self):
    self._makeComputeNode()
    software_installation = self.portal\
       .software_installation_module.template_software_installation\
       .Base_createCloneDocument(batch_mode=1)
    software_installation.edit(
       url_string=self.generateNewSoftwareReleaseUrl(),
       aggregate=self.compute_node.getRelativeUrl(),
       reference='TESTSOFTINSTS-%s' % self.generateNewId(),
       title='Start requested for %s' % self.compute_node.getUid()
     )
    software_installation.validate()
    software_installation.requestStart()

    return software_installation

class TestSlapOSSupportRequestModule_getMonitoringUrlList(TestCRMSkinsMixin):

  def test_SupportRequestModule_getMonitoringUrlList(self):
    module = self.portal.support_request_module
    # We assume here that several objects created by others tests don't influentiate
    # this test.
    self.assertEqual(module.SupportRequestModule_getMonitoringUrlList(), [])
    instance_tree = self._makeInstanceTree()
    self._makeSoftwareInstance(instance_tree, "https://xxx/")
    support_request = module.newContent(portal_type="Support Request")
    self.tic()

    self.assertEqual(module.SupportRequestModule_getMonitoringUrlList(), [])
    support_request.setAggregateValue(instance_tree)
    support_request.validate()
    self.assertNotEqual(instance_tree.getSuccessorList(), [])

    self.tic()
    self.assertEqual(module.SupportRequestModule_getMonitoringUrlList(), [])
    
    instance = instance_tree.getSuccessorValue()
    instance.setConnectionXml("""<?xml version='1.0' encoding='utf-8'?>
<instance>
  <parameter id="aa">xx</parameter>
  <parameter id="bb">yy</parameter>
</instance>
    """)
    self.assertEqual(module.SupportRequestModule_getMonitoringUrlList(), [])
    instance.setConnectionXml("""<?xml version='1.0' encoding='utf-8'?>
<instance>
  <parameter id="monitor-setup-url">http</parameter>
  <parameter id="bb">yy</parameter>
</instance>
    """)
    self.assertEqual(module.SupportRequestModule_getMonitoringUrlList(), [])

    self.assertEqual(module.SupportRequestModule_getMonitoringUrlList(), [])
    instance.setConnectionXml("""<?xml version='1.0' encoding='utf-8'?>
<instance>
  <parameter id="monitor-setup-url">http://monitor.url/#/ABC</parameter>
  <parameter id="bb">yy</parameter>
</instance>
    """)

    monitor_url_temp_document_list = module.SupportRequestModule_getMonitoringUrlList()
    self.assertEqual(len(monitor_url_temp_document_list), 1)
    self.assertEqual(monitor_url_temp_document_list[0].title,
                     instance_tree.getTitle())
    self.assertEqual(monitor_url_temp_document_list[0].monitor_url,
                     "http://monitor.url/#/ABC")
    support_request.invalidate()
    self.tic()
    self.assertNotEqual(instance_tree.getSuccessorList(), [])

class TestComputeNode_hasContactedRecently(SlapOSTestCaseMixinWithAbort):

  def createSPL(self, compute_node):
    delivery_template = self.portal.restrictedTraverse(
      self.portal.portal_preferences.getPreferredInstanceDeliveryTemplate())
    delivery = delivery_template.Base_createCloneDocument(batch_mode=1)

    delivery.edit(
      title="TEST SPL COMP %s" % compute_node.getReference(),
      start_date=compute_node.getCreationDate(),
    )

    delivery.newContent(
      portal_type="Sale Packing List Line",
      title="SPL Line for %s" % compute_node.getReference(),
      quantity=1,
      aggregate_value_list=compute_node,
    )
    delivery.confirm(comment="Created from %s" % compute_node.getRelativeUrl())
    delivery.start()
    delivery.stop()
    delivery.deliver()
    return delivery

  def test_ComputeNode_hasContactedRecently_newly_created(self):
    compute_node = self._makeComputeNode()[0]
    self.tic()
    has_contacted = compute_node.ComputeNode_hasContactedRecently()
    self.assertTrue(has_contacted)

  @simulate('ComputeNode_getCreationDate', '*args, **kwargs','return DateTime() - 32')
  def test_ComputeNode_hasContactedRecently_no_data(self):
    compute_node = self._makeComputeNode()[0]
    self.tic()

    compute_node.getCreationDate = self.portal.ComputeNode_getCreationDate
    has_contacted = compute_node.ComputeNode_hasContactedRecently()
    self.assertFalse(has_contacted)

  @simulate('ComputeNode_getCreationDate', '*args, **kwargs','return DateTime() - 32')
  def test_ComputeNode_hasContactedRecently_memcached(self):
    compute_node = self._makeComputeNode()[0]
    compute_node.setAccessStatus("")
    self.tic()

    compute_node.getCreationDate = self.portal.ComputeNode_getCreationDate

    has_contacted = compute_node.ComputeNode_hasContactedRecently()
    self.assertTrue(has_contacted)

  @simulate('ComputeNode_getCreationDate', '*args, **kwargs','return DateTime() - 32')
  def test_ComputeNode_hasContactedRecently_memcached_oudated_no_spl(self):
    compute_node = self._makeComputeNode()[0]
    try:
      self.pinDateTime(DateTime()-32)
      compute_node.setAccessStatus("")
    finally:
      self.unpinDateTime()

    self.tic()

    compute_node.getCreationDate = self.portal.ComputeNode_getCreationDate

    has_contacted = compute_node.ComputeNode_hasContactedRecently()
    self.assertFalse(has_contacted)

  @simulate('ComputeNode_getCreationDate', '*args, **kwargs','return DateTime() - 32')
  def test_ComputeNode_hasContactedRecently_memcached_oudated_with_spl(self):
    compute_node = self._makeComputeNode()[0]
    try:
      self.pinDateTime(DateTime()-32)
      compute_node.setAccessStatus("")
    finally:
      self.unpinDateTime()

    self.createSPL(compute_node)
    self.tic()

    compute_node.getCreationDate = self.portal.ComputeNode_getCreationDate

    has_contacted = compute_node.ComputeNode_hasContactedRecently()
    self.assertFalse(has_contacted)

class TestSlapOSisSupportRequestCreationClosed(TestCRMSkinsMixin):

  def afterSetUp(self):
    TestCRMSkinsMixin.afterSetUp(self)
    self._cancelTestSupportRequestList()
    self.clearCache()

  def test_ERP5Site_isSupportRequestCreationClosed(self):

    person = self.makePerson(user=0)
    other_person = self.makePerson(user=0)
    url = person.getRelativeUrl()
    self.assertFalse(self.portal.ERP5Site_isSupportRequestCreationClosed(url))
    self.assertFalse(self.portal.ERP5Site_isSupportRequestCreationClosed())
    self.portal.portal_preferences.slapos_default_system_preference\
      .setPreferredSupportRequestCreationLimit(5)

    def newSupportRequest():
      sr = self.portal.support_request_module.newContent(\
                        title="Test Support Request POIUY",
                        resource="service_module/slapos_crm_monitoring",
                        destination_decision=url)
      sr.validate()
      sr.immediateReindexObject()

    newSupportRequest()
    self.assertFalse(self.portal.ERP5Site_isSupportRequestCreationClosed(url))
    newSupportRequest()
    self.assertFalse(self.portal.ERP5Site_isSupportRequestCreationClosed(url))
    newSupportRequest()
    self.assertFalse(self.portal.ERP5Site_isSupportRequestCreationClosed(url))
    newSupportRequest()
    self.assertFalse(self.portal.ERP5Site_isSupportRequestCreationClosed(url))
    newSupportRequest()
    # It hit cache
    self.assertFalse(self.portal.ERP5Site_isSupportRequestCreationClosed(url))
    self.clearCache() 
    self.assertTrue(self.portal.ERP5Site_isSupportRequestCreationClosed(url))

    self.assertTrue(self.portal.ERP5Site_isSupportRequestCreationClosed())

    self.assertFalse(self.portal.ERP5Site_isSupportRequestCreationClosed(
                     other_person.getRelativeUrl()))

  def test_ERP5Site_isSupportRequestCreationClosed_suspended_state(self):
    person = self.makePerson(user=0)
    url = person.getRelativeUrl()
    self.assertFalse(self.portal.ERP5Site_isSupportRequestCreationClosed(url))
    self.assertFalse(self.portal.ERP5Site_isSupportRequestCreationClosed())

    def newSupportRequest():
      sr = self.portal.support_request_module.newContent(\
                        title="Test Support Request POIUY",
                        resource="service_module/slapos_crm_monitoring",
                        destination_decision=url)
      sr.validate()
      sr.suspend()
      sr.immediateReindexObject()
    # Create five tickets, the limit of ticket creation
    newSupportRequest()
    newSupportRequest()
    newSupportRequest()
    newSupportRequest()
    newSupportRequest()
    self.assertFalse(self.portal.ERP5Site_isSupportRequestCreationClosed(url))
    self.assertFalse(self.portal.ERP5Site_isSupportRequestCreationClosed())


  def test_ERP5Site_isSupportRequestCreationClosed_nonmonitoring(self):
    person = self.makePerson(user=0)
    url = person.getRelativeUrl()
    self.assertFalse(self.portal.ERP5Site_isSupportRequestCreationClosed(url))
    self.assertFalse(self.portal.ERP5Site_isSupportRequestCreationClosed())

    def newSupportRequest():
      sr = self.portal.support_request_module.newContent(\
                        title="Test Support Request POIUY",
                        destination_decision=url)
      sr.validate()
      sr.immediateReindexObject()

    # Create five tickets, the limit of ticket creation
    newSupportRequest()
    newSupportRequest()
    newSupportRequest()
    newSupportRequest()
    newSupportRequest()

    self.assertFalse(self.portal.ERP5Site_isSupportRequestCreationClosed(url))
    self.assertFalse(self.portal.ERP5Site_isSupportRequestCreationClosed())


class TestSlapOSComputeNode_CheckState(TestCRMSkinsMixin):

  def beforeTearDown(self):
    self._cancelTestSupportRequestList()
    transaction.abort()

  def afterSetUp(self):
    TestCRMSkinsMixin.afterSetUp(self)
    self._cancelTestSupportRequestList("% TESTCOMPT-%")

  def _makeNotificationMessage(self, reference):
    notification_message = self.portal.notification_message_module.newContent(
      portal_type="Notification Message",
      title='The Compute Node %s has not contacted the server for more than 24 hours' % reference,
      text_content='Test NM content<br/>%s<br/>' % reference,
      content_type='text/html',
      )

    return notification_message.getRelativeUrl()

  def _getGeneratedSupportRequest(self, compute_node_uid, request_title):
    support_request = self.portal.portal_catalog.getResultValue(
          portal_type = 'Support Request',
          title = request_title,
          simulation_state = 'validated',
          default_aggregate_uid = compute_node_uid
    )
    return support_request

  @simulate('ERP5Site_isSupportRequestCreationClosed', '*args, **kwargs','return 0')
  def test_ComputeNode_checkState_call_support_request(self):
    compute_node = self._makeComputeNode(owner=self.makePerson(user=0))[0]
    try:
      d = DateTime() - 1.1
      self.pinDateTime(d)
      compute_node.setAccessStatus("")
    finally:
      self.unpinDateTime()

    compute_node_support_request = compute_node.ComputeNode_checkState()
    self.assertNotEqual(compute_node_support_request, None)
    self.assertIn("[MONITORING] Lost contact with compute_node",
      compute_node_support_request.getTitle())
    self.assertIn("has not contacted the server for more than 30 minutes",
      compute_node_support_request.getDescription())
    self.assertIn(d.strftime("%Y/%m/%d %H:%M:%S"),
      compute_node_support_request.getDescription())

  @simulate('ERP5Site_isSupportRequestCreationClosed', '*args, **kwargs','return 0')
  def test_ComputeNode_checkState_empty_cache(self):
    compute_node = self._makeComputeNode(owner=self.makePerson(user=0))[0]
    compute_node_support_request = compute_node.ComputeNode_checkState()
    
    compute_node_support_request = compute_node.ComputeNode_checkState()
    self.assertNotEqual(compute_node_support_request, None)
    self.assertIn("[MONITORING] Lost contact with compute_node",
      compute_node_support_request.getTitle())
    self.assertIn("has not contacted the server (No Contact Information)",
      compute_node_support_request.getDescription())

  @simulate('ERP5Site_isSupportRequestCreationClosed', '*args, **kwargs','return 0')
  @simulate('NotificationTool_getDocumentValue',
            'reference=None',
  'assert reference == "slapos-crm-compute_node_check_state.notification"\n' \
  'return context.restrictedTraverse(' \
  'context.REQUEST["test_ComputeNode_checkState_notify"])')
  def test_ComputeNode_checkState_notify(self):
    compute_node = self._makeComputeNode(owner=self.makePerson(user=0))[0]
    person = compute_node.getSourceAdministrationValue()

    try:
      self.pinDateTime(DateTime()-1.1)
      compute_node.setAccessStatus("")
    finally:
      self.unpinDateTime()

    self.portal.REQUEST['test_ComputeNode_checkState_notify'] = \
        self._makeNotificationMessage(compute_node.getReference())

    compute_node.ComputeNode_checkState()
    self.tic()

    ticket_title = "[MONITORING] Lost contact with compute_node %s" % compute_node.getReference()
    ticket = self._getGeneratedSupportRequest(compute_node.getUid(), ticket_title)

    self.assertNotEqual(ticket, None)
    event_list = ticket.getFollowUpRelatedValueList()
    self.assertEqual(len(event_list), 1)
    event = event_list[0]

    self.assertEqual(event.getTitle(), ticket.getTitle())
    self.assertIn(compute_node.getReference(), event.getTextContent())
    self.assertEqual(event.getSource(), person.getRelativeUrl())
    self.assertEqual(event.getDestination(), ticket.getSourceSection())


  @simulate('ERP5Site_isSupportRequestCreationClosed', '*args, **kwargs','return 0')
  @simulate('NotificationTool_getDocumentValue',
            'reference=None',
  'assert reference == "slapos-crm-compute_node_check_state.notification"\n' \
  'return context.restrictedTraverse(' \
  'context.REQUEST["test_ComputeNode_checkState_empty_cache_notify"])')
  def test_ComputeNode_checkState_empty_cache_notify(self):
    compute_node = self._makeComputeNode(owner=self.makePerson(user=0))[0]
    person = compute_node.getSourceAdministrationValue()

    self.portal.REQUEST['test_ComputeNode_checkState_empty_cache_notify'] = \
        self._makeNotificationMessage(compute_node.getReference())

    compute_node.ComputeNode_checkState()
    self.tic()

    ticket_title = "[MONITORING] Lost contact with compute_node %s" % compute_node.getReference()
    ticket = self._getGeneratedSupportRequest(compute_node.getUid(), ticket_title)
    self.assertNotEqual(ticket, None)
    event_list = ticket.getFollowUpRelatedValueList()
    self.assertEqual(len(event_list), 1)
    event = event_list[0]

    self.assertEqual(event.getTitle(), ticket.getTitle())
    self.assertIn(compute_node.getReference(), event.getTextContent())
    self.assertEqual(event.getDestination(), ticket.getSourceSection())
    self.assertEqual(event.getSource(), person.getRelativeUrl())

  @simulate('ERP5Site_isSupportRequestCreationClosed', '*args, **kwargs','return 0')
  @simulate('NotificationTool_getDocumentValue',
            'reference=None',
  'assert reference == "slapos-crm-compute_node_check_stalled_instance_state.notification", reference\n' \
  'return context.restrictedTraverse(' \
  'context.REQUEST["test_ComputeNode_checkState_stalled_instance"])')
  def test_ComputeNode_checkState_stalled_instance(self):
    compute_node = self._makeComputeNode(owner=self.makePerson(user=0))[0]
    self._makeComplexComputeNode()

    person = compute_node.getSourceAdministrationValue()

    self.portal.REQUEST['test_ComputeNode_checkState_stalled_instance'] = \
        self._makeNotificationMessage(compute_node.getReference())

    # Computer is getting access
    compute_node.setAccessStatus("")

    try:
      self.pinDateTime(DateTime()-1.1)
      self.start_requested_software_instance.setAccessStatus("")
    finally:
      self.unpinDateTime()

    compute_node.ComputeNode_checkState()
    self.tic()

    ticket_title = "[MONITORING] Compute Node %s has a stalled instance process" % compute_node.getReference()
    ticket = self._getGeneratedSupportRequest(compute_node.getUid(), ticket_title)
    self.assertNotEqual(ticket, None)
    event_list = ticket.getFollowUpRelatedValueList()
    self.assertEqual(len(event_list), 1)
    event = event_list[0]

    self.assertEqual(event.getTitle(), ticket.getTitle())
    self.assertIn(compute_node.getReference(), event.getTextContent())
    self.assertEqual(event.getDestination(), ticket.getSourceSection())
    self.assertEqual(event.getSource(), person.getRelativeUrl())


  @simulate('ERP5Site_isSupportRequestCreationClosed', '*args, **kwargs','return 0')
  @simulate('NotificationTool_getDocumentValue',
            'reference=None',
  'assert reference == "slapos-crm-compute_node_check_stalled_instance_state.notification", reference\n' \
  'return context.restrictedTraverse(' \
  'context.REQUEST["test_ComputeNode_checkState_stalled_instance"])')
  def test_ComputeNode_checkState_stalled_instance_single(self):
    compute_node = self._makeComputeNode(owner=self.makePerson(user=0))[0]
    self._makeComplexComputeNode()

    person = compute_node.getSourceAdministrationValue()

    self.portal.REQUEST['test_ComputeNode_checkState_stalled_instance'] = \
        self._makeNotificationMessage(compute_node.getReference())

    # Computer is getting access
    compute_node.setAccessStatus("")

    try:
      self.pinDateTime(DateTime()-1.1)
      self.start_requested_software_instance.setAccessStatus("")
      self.start_requested_software_installation.setAccessStatus("")
    finally:
      self.unpinDateTime()

    compute_node.ComputeNode_checkState()
    self.tic()

    ticket_title = "[MONITORING] Compute Node %s has a stalled instance process" % compute_node.getReference()
    ticket = self._getGeneratedSupportRequest(compute_node.getUid(), ticket_title)
    self.assertNotEqual(ticket, None)
    event_list = ticket.getFollowUpRelatedValueList()
    self.assertEqual(len(event_list), 1)
    event = event_list[0]

    self.assertEqual(event.getTitle(), ticket.getTitle())
    self.assertIn(compute_node.getReference(), event.getTextContent())
    self.assertEqual(event.getDestination(), ticket.getSourceSection())
    self.assertEqual(event.getSource(), person.getRelativeUrl())

class TestSlapOSInstanceTree_createSupportRequestEvent(SlapOSTestCaseMixin):

  def _makeNotificationMessage(self, reference):
    notification_message = self.portal.notification_message_module.newContent(
      portal_type="Notification Message",
      title='%s created an event' % reference,
      text_content='Test NM content<br/>%s<br/>' % reference,
      content_type='text/html',
      )

    return notification_message.getRelativeUrl()

  def _makeInstanceTree(self):
    person = self.makePerson(user=1)
    instance_tree = self.portal\
      .instance_tree_module.template_instance_tree\
      .Base_createCloneDocument(batch_mode=1)
    instance_tree.validate()
    new_id = self.generateNewId()
    instance_tree.edit(
        title= "Test hosting sub ticket %s" % new_id,
        reference="TESTHST-%s" % new_id,
        destination_section_value=person
    )

    return instance_tree

  def _getGeneratedSupportRequest(self, instance_tree_uid):
    support_request = self.portal.portal_catalog.getResultValue(
          portal_type = 'Support Request',
          simulation_state = "validated",
          default_aggregate_uid = instance_tree_uid
    )
    return support_request

  @simulate('ERP5Site_isSupportRequestCreationClosed', '*args, **kwargs','return 0')
  @simulate('SoftwareInstance_hasReportedError', '*args, **kwargs','return "MSG"')
  @simulate('NotificationTool_getDocumentValue',
            'reference=None',
  'assert reference == "test-slapos-crm-check.notification"\n' \
  'return context.restrictedTraverse(' \
  'context.REQUEST["testInstanceTree_createSupportRequestEvent"])')
  def testInstanceTree_createSupportRequestEvent(self):
    instance_tree = self._makeInstanceTree()
    person =  instance_tree.getDestinationSectionValue()
    self.portal.REQUEST['testInstanceTree_createSupportRequestEvent'] = \
        self._makeNotificationMessage(instance_tree.getReference())

    instance_tree.InstanceTree_createSupportRequestEvent(
      instance_tree, "test-slapos-crm-check.notification")

    self.tic()
    ticket_title = "Instance Tree %s is failing." % instance_tree.getTitle()
    ticket = self._getGeneratedSupportRequest(
      instance_tree.getUid())
    self.assertNotEqual(ticket, None)
    self.assertEqual(ticket.getSimulationState(), "validated")
    self.assertNotEqual(ticket, None)
    event_list = ticket.getFollowUpRelatedValueList()
    self.assertEqual(len(event_list), 1)
    event = event_list[0]

    self.assertEqual(event.getTitle(), ticket_title)
    self.assertIn(instance_tree.getReference(), event.getTextContent())
    self.assertEqual(event.getSource(), person.getRelativeUrl())
    self.assertEqual(event.getDestination(), ticket.getSourceSection())

    ticket.suspend()
    self.tic()
    self.assertEqual(None, self._getGeneratedSupportRequest(
      instance_tree.getUid()))

    instance_tree.InstanceTree_createSupportRequestEvent(
      instance_tree, "test-slapos-crm-check.notification")
    self.tic()

    ticket = self._getGeneratedSupportRequest(
      instance_tree.getUid())
    # Do not reopen the ticket if it is suspended
    self.assertEqual(None, ticket)

  @simulate('ERP5Site_isSupportRequestCreationClosed', '*args, **kwargs','return 1')
  @simulate('SoftwareInstance_hasReportedError', '*args, **kwargs','return "MSG"')
  def testInstanceTree_createSupportRequestEvent_closed(self):
    instance_tree = self._makeInstanceTree()
    self.assertEqual(None,
      instance_tree.InstanceTree_createSupportRequestEvent(
         instance_tree, "test-slapos-crm-check.notification"))

  @simulate('ERP5Site_isSupportRequestCreationClosed', '*args, **kwargs','return 0')
  @simulate('SoftwareInstance_hasReportedError', '*args, **kwargs','return "MSG"')
  def testInstanceTree_createSupportRequestEvent_no_person(self):
    instance_tree = self._makeInstanceTree()
    instance_tree.setDestinationSectionValue(None)
    self.assertEqual(None,
      instance_tree.InstanceTree_createSupportRequestEvent(
         instance_tree, "test-slapos-crm-check.notification"))

class TestSlapOSHasError(SlapOSTestCaseMixin):

  def _makeSoftwareRelease(self, software_release_url=None):
    software_release = self.portal.software_release_module\
      .template_software_release.Base_createCloneDocument(batch_mode=1)

    new_id = self.generateNewId()
    software_release.edit(
      url_string=software_release_url or self.generateNewSoftwareReleaseUrl(),
      reference='TESTSOFTRELS-%s' % new_id,
      title='Start requested for %s' % new_id
    )
    software_release.release()

    return software_release

  def _makeSoftwareInstallation(self, software_release_url):
    software_installation = self.portal\
       .software_installation_module.template_software_installation\
       .Base_createCloneDocument(batch_mode=1)

    new_id = self.generateNewId()
    software_installation.edit(
       url_string=software_release_url,
       aggregate=self.compute_node.getRelativeUrl(),
       reference='TESTSOFTINSTS-%s' % new_id,
       title='Start requested for %s' % self.compute_node.getUid()
     )
    software_installation.validate()
    software_installation.requestStart()

    return software_installation

  def _makeSoftwareInstance(self, instance_tree, software_url):

    kw = dict(
      software_release=software_url,
      software_type=self.generateNewSoftwareType(),
      instance_xml=self.generateSafeXml(),
      sla_xml=self.generateSafeXml(),
      shared=False,
      software_title=instance_tree.getTitle(),
      state='started'
    )
    instance_tree.requestStart(**kw)
    instance_tree.requestInstance(**kw)

  def _makeInstanceTree(self):
    person = self.portal.person_module.template_member\
         .Base_createCloneDocument(batch_mode=1)
    instance_tree = self.portal\
      .instance_tree_module.template_instance_tree\
      .Base_createCloneDocument(batch_mode=1)
    instance_tree.validate()
    new_id = self.generateNewId()
    instance_tree.edit(
        title="Test hosting sub ticket %s" % new_id,
        reference="TESTHST-%s" % new_id,
        destination_section_value=person,
        monitor_scope="enabled"
    )

    return instance_tree

  def _makeComputePartitionList(self):
    for i in range(1, 5):
      id_ = 'partition%s' % (i, )
      p = self.compute_node.newContent(portal_type='Compute Partition',
        id=id_,
        title=id_,
        reference=id_,
        default_network_address_ip_address='ip_address_%s' % i,
        default_network_address_netmask='netmask_%s' % i)
      p.markFree()
      p.validate()

  def test_SoftwareInstance_hasReportedError(self):
    instance_tree = self._makeInstanceTree()
    self._makeSoftwareInstance(instance_tree, 
        self.generateNewSoftwareReleaseUrl())
    instance = instance_tree.getSuccessorValue()

    self._makeComputeNode()
    self._makeComputePartitionList()

    instance.setErrorStatus("")
  
    self.assertEqual(instance.SoftwareInstance_hasReportedError(), None)

    instance.setAggregateValue(self.compute_node.partition1)

    self.assertEqual(str(instance.SoftwareInstance_hasReportedError()), '#error ')

    instance.setAccessStatus("")
    self.assertEqual(instance.SoftwareInstance_hasReportedError(), None)

  def test_SoftwareInstallation_hasReportedError(self):
    software_release = self._makeSoftwareRelease()
    self._makeComputeNode()
    installation = self._makeSoftwareInstallation(
      software_release.getUrlString()
    )

    self.assertEqual(installation.SoftwareInstallation_hasReportedError(), None)

    error_date = DateTime()
    try:
      self.pinDateTime(error_date)
      installation.setErrorStatus("")
    finally:
      self.unpinDateTime()

    self.assertEqual(
      rfc1123_date(installation.SoftwareInstallation_hasReportedError()),
      rfc1123_date(error_date))
    installation.setBuildingStatus("")

    self.assertEqual(installation.SoftwareInstallation_hasReportedError(), None)

  @simulate('ERP5Site_isSupportRequestCreationClosed', '','return 0')
  @simulate('InstanceTree_createSupportRequestEvent',
            'instance, notification_message_reference',
  'return "Visited by InstanceTree_createSupportRequestEvent ' \
  '%s %s" % (instance.getUid(), notification_message_reference)')
  def testInstanceTree_checkSoftwareInstanceState(self):
    date = DateTime()
    def getCreationDate(*args, **kwargs):
      return date - 2

    from Products.ERP5Type.Base import Base

    original_get_creation = Base.getCreationDate
    Base.getCreationDate = getCreationDate
    try:
      instance_tree = self._makeInstanceTree()

      self.assertEqual(instance_tree.getCreationDate(), date - 2)

      self._makeSoftwareInstance(instance_tree,
          self.generateNewSoftwareReleaseUrl())
      instance = instance_tree.getSuccessorValue()

      self.assertEqual(instance.getCreationDate(), date - 2)

      self._makeComputeNode()
      self._makeComputePartitionList()
      instance.setAggregateValue(self.compute_node.partition1)

      error_date = DateTime()
      value = json.dumps(
        {"created_at":"%s" % error_date, "text": "#error ", "since": "%s" % (error_date - 2)}
      )
      cache_duration = instance._getAccessStatusCacheFactory().cache_duration
      instance._getAccessStatusPlugin().set(instance._getAccessStatusCacheKey(),
        DEFAULT_CACHE_SCOPE, value, cache_duration=cache_duration)

      self.assertEqual(
        'Visited by InstanceTree_createSupportRequestEvent %s %s' % \
        (instance.getUid(),
         "slapos-crm-instance-tree-instance-state.notification"),
        instance_tree.InstanceTree_checkSoftwareInstanceState())

      instance.setAccessStatus("")

      self.assertEqual(None,
        instance_tree.InstanceTree_checkSoftwareInstanceState())


    finally:
      Base.getCreationDate = original_get_creation

      self.portal.portal_types.resetDynamicDocumentsOnceAtTransactionBoundary()
      transaction.commit()


  @simulate('ERP5Site_isSupportRequestCreationClosed', '','return 0')
  @simulate('InstanceTree_createSupportRequestEvent',
            'instance, notification_message_reference',
  'return "Visited by InstanceTree_createSupportRequestEvent ' \
  '%s %s" % (instance.getUid(), notification_message_reference)')
  def testInstanceTree_checkSoftwareInstanceState_tolerance(self):
    date = DateTime()
    def getCreationDate(*args, **kwargs):
      return date - 2

    from Products.ERP5Type.Base import Base

    original_get_creation = Base.getCreationDate
    Base.getCreationDate = getCreationDate
    try:
      instance_tree = self._makeInstanceTree()

      self.assertEqual(instance_tree.getCreationDate(), date - 2)

      self._makeSoftwareInstance(instance_tree,
          self.generateNewSoftwareReleaseUrl())
      instance = instance_tree.getSuccessorValue()

      self.assertEqual(instance.getCreationDate(), date - 2)

      self._makeComputeNode()
      self._makeComputePartitionList()
      instance.setAggregateValue(self.compute_node.partition1)

      memcached_dict = self.portal.portal_memcached.getMemcachedDict(
        key_prefix='slap_tool',
        plugin_path='portal_memcached/default_memcached_plugin')

      error_date = DateTime()
      memcached_dict[instance.getReference()] = json.dumps(
        {"created_at":"%s" % error_date, "text": "#error ", "since": "%s" % error_date}
      )

      # With tolerance of 30 min this should create SupportRequests immediately
      self.assertEqual(None,
        instance_tree.InstanceTree_checkSoftwareInstanceState())

    finally:
      Base.getCreationDate = original_get_creation

      self.portal.portal_types.resetDynamicDocumentsOnceAtTransactionBoundary()
      transaction.commit()


  @simulate('ERP5Site_isSupportRequestCreationClosed', '','return 0')
  @simulate('InstanceTree_createSupportRequestEvent',
            'instance, notification_message_reference',
  'return "Visited by InstanceTree_createSupportRequestEvent ' \
  '%s %s" % (instance.getRelativeUrl(), notification_message_reference)')
  def testInstanceTree_checkSoftwareInstanceState_partially_allocation(self):
    date = DateTime()
    def getCreationDate(*args, **kwargs):
      return date - 2

    from Products.ERP5Type.Base import Base

    original_get_creation = Base.getCreationDate
    Base.getCreationDate = getCreationDate
    try:
      instance_tree = self._makeInstanceTree()

      self.assertEqual(instance_tree.getCreationDate(), date - 2)

      self._makeSoftwareInstance(instance_tree,
          self.generateNewSoftwareReleaseUrl())
      instance = instance_tree.getSuccessorValue()

      self.assertEqual(instance.getCreationDate(), date - 2)

      self._makeComputeNode()
      self._makeComputePartitionList()
      instance.setAggregateValue(self.compute_node.partition1)

      kw = dict(
        software_release=instance_tree.getUrlString(),
        software_type=self.generateNewSoftwareType(),
        instance_xml=self.generateSafeXml(),
        sla_xml=self.generateSafeXml(),
        shared=False,
        software_title="Another INstance %s" % self.generateNewId(),
        state='started'
      )
      instance.requestInstance(**kw)
      self.tic()

      instance.setAccessStatus("")

      self.assertEqual(
        'Visited by InstanceTree_createSupportRequestEvent %s %s' % \
        (instance.getSuccessor(portal_type="Software Instance"),
         "slapos-crm-instance-tree-instance-allocation.notification"),
        instance_tree.InstanceTree_checkSoftwareInstanceState())

      kw["state"] = "destroyed"
      instance.requestInstance(**kw)
      self.tic()

      self.assertEqual(
        None,
        instance_tree.InstanceTree_checkSoftwareInstanceState())

    finally:
      Base.getCreationDate = original_get_creation

      self.portal.portal_types.resetDynamicDocumentsOnceAtTransactionBoundary()
      transaction.commit()

  @simulate('ERP5Site_isSupportRequestCreationClosed', '','return 0')
  def testInstanceTree_checkSoftwareInstanceState_too_early(self):
    instance_tree = self._makeInstanceTree()

    self._makeSoftwareInstance(instance_tree,
        self.generateNewSoftwareReleaseUrl())
    instance = instance_tree.getSuccessorValue()


    self._makeComputeNode()
    self._makeComputePartitionList()
    instance.setAggregateValue(self.compute_node.partition1)

    instance.setErrorStatus("")
    self.assertEqual(
        None,
        instance_tree.InstanceTree_checkSoftwareInstanceState())


class TestCRMPropertySheetConstraint(SlapOSTestCaseMixin):

  def afterSetUp(self):
    SlapOSTestCaseMixin.afterSetUp(self)
    portal = self.getPortalObject()

    self.ticket_trade_condition = portal.sale_trade_condition_module.slapos_ticket_trade_condition

    person_user = self.makePerson()
    self.tic()

    # Login as new user
    self.login(person_user.getUserId())

    new_person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()
    self.assertEqual(person_user.getRelativeUrl(), new_person.getRelativeUrl())

    self.support_request = portal.support_request_module.newContent(
      portal_type="Support Request",
      destination_decision=person_user.getRelativeUrl(),
      specialise=self.ticket_trade_condition.getRelativeUrl()
    )

    # Value set by the init
    self.assertTrue(self.support_request.getReference().startswith("SR-"),
      "Reference don't start with SR- : %s" % self.support_request.getReference())

  def beforeTearDown(self):
    transaction.abort()

  def testCheckCausalitySourceDestinationConsistency(self):
    person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()

    self.support_request.approveRegistration()
    self.tic()

    self.logout()
    self.login()

    event = self.support_request.getCausalityValue()
    self.assertNotEqual(event, None)

    self.assertFalse(event.checkConsistency())
    self.assertFalse(self.support_request.checkConsistency())

    source = event.getDestination()
    event.setDestination(person.getRelativeUrl())

    non_consistency_list = [str(i.getTranslatedMessage()) for i in self.support_request.checkConsistency()]
    self.assertEqual(non_consistency_list,
      ['Destination  of the related event should be the slapos organisation'])

    event.setSource(source)
    non_consistency_list = [str(i.getTranslatedMessage()) for i in self.support_request.checkConsistency()]
    self.assertEqual(non_consistency_list,
      ['Sender of the related event should be the customer',
       'Destination  of the related event should be the slapos organisation'])    
    

  def testCheckCustomerAsSourceOrDestinationConsistency(self):
    person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()

    self.support_request.approveRegistration()
    self.tic()

    self.logout()
    self.login()

    event = self.support_request.getCausalityValue()
    self.assertNotEqual(event, None)

    self.assertFalse(event.checkConsistency())
    self.assertFalse(self.support_request.checkConsistency())

    person_user = self.makePerson()
    self.tic()

    event.setSource(person_user.getRelativeUrl())

    non_consistency_list = [str(i.getTranslatedMessage()) for i in event.checkConsistency()]
    self.assertEqual(non_consistency_list, [
      'Customer should be source or destination of the event'
    ])

    event.setDestination(person.getRelativeUrl())
    self.assertFalse(event.checkConsistency())

class TestSupportRequestUpdateMonitoringState(SlapOSTestCaseMixin):

  def _makeInstanceTree(self):
    person = self.portal.person_module.template_member\
         .Base_createCloneDocument(batch_mode=1)
    instance_tree = self.portal\
      .instance_tree_module.template_instance_tree\
      .Base_createCloneDocument(batch_mode=1)
    instance_tree.validate()
    new_id = self.generateNewId()
    instance_tree.edit(
        title="Test hosting sub ticket %s" % new_id,
        reference="TESTHST-%s" % new_id,
        destination_section_value=person
    )

    return instance_tree

  def _makeSupportRequest(self):
    return self.portal.restrictedTraverse(
        self.portal.portal_preferences.getPreferredSupportRequestTemplate()).\
       Base_createCloneDocument(batch_mode=1)

  @simulate('ERP5Site_isSupportRequestCreationClosed', '','return 0')
  @simulate('SupportRequest_updateMonitoringDestroyRequestedState',
            "",
    'return "Visited by SupportRequest_updateMonitoringDestroyRequestedState '\
    '%s" % (context.getRelativeUrl(),)')
  def testSupportRequest_updateMonitoringState(self):
    support_request = self._makeSupportRequest()
    self.assertEqual(None,
      support_request.SupportRequest_updateMonitoringState())
    support_request.validate()
    self.assertEqual(None,
      support_request.SupportRequest_updateMonitoringState())
    
    hs = self._makeInstanceTree()
    support_request.setAggregateValue(hs)
    hs.getSlapState = getFakeSlapState

    self.assertEqual(
      "Visited by SupportRequest_updateMonitoringDestroyRequestedState %s" %\
        support_request.getRelativeUrl(),
      support_request.SupportRequest_updateMonitoringState())

    support_request.invalidate()
    self.assertEqual(None,
      support_request.SupportRequest_updateMonitoringState())

  @simulate('ERP5Site_isSupportRequestCreationClosed', '','return 0')
  def testSupportRequest_updateMonitoringDestroyRequestedState(self):
    support_request = self._makeSupportRequest()
    self.assertEqual(None,
      support_request.SupportRequest_updateMonitoringDestroyRequestedState())
    support_request.validate()
    self.assertEqual(None,
      support_request.SupportRequest_updateMonitoringDestroyRequestedState())

    support_request.setAggregateValue(
      self._makeComputeNode(owner=self.makePerson(user=0))[0])
    support_request.setDestinationDecisionValue(self.makePerson(user=0))
    self.assertEqual(None,
      support_request.SupportRequest_updateMonitoringDestroyRequestedState())

    hs = self._makeInstanceTree()
    support_request.setAggregateValue(hs)

    self.tic()

    hs.getSlapState = getFakeSlapState
    self.commit()

    self.assertNotEqual(None,
      support_request.SupportRequest_updateMonitoringDestroyRequestedState())

    self.tic()
    event_list = support_request.getFollowUpRelatedValueList()
    self.assertEqual(len(event_list), 1)
    event = event_list[0]

    self.assertEqual(event.getTitle(), 'Instance Tree was destroyed was destroyed by the user')
    self.assertEqual(event.getSource(), support_request.getDestinationDecision())
    self.assertEqual(event.getDestination(), support_request.getSourceSection())

    self.assertEqual("invalidated",
      support_request.getSimulationState())


class TestSlapOSFolder_getTicketFeedUrl(TestCRMSkinsMixin):

  def _test(self, module):
    self.assertRaises(ValueError, module.Folder_getTicketFeedUrl)
    person = self.makePerson(user=1)
    self.tic()
    
    self.login(person.getUserId())

    url = module.Folder_getTicketFeedUrl()
    self.assertIn('Folder_viewOpenTicketList', url)
    self.assertIn(module.absolute_url(), url)
    self.assertIn('access_token_secret', url)
    self.assertIn('access_token=', url)
    self.assertIn('portal_skin=RSS', url)

    self.tic()
    self.assertEqual(url, module.Folder_getTicketFeedUrl())

  def test_Folder_getTicketFeedUrl_support_request_module(self):
    self._test(self.portal.support_request_module)

  def test_Folder_getTicketFeedUrl_regularisation_request_module(self):
    self._test(self.portal.regularisation_request_module)

  def test_Folder_getTicketFeedUrl_incident_response_module(self):
    self._test(self.portal.incident_response_module)


class TestSlapOSPerson_getSlapOSPendingTicket(TestCRMSkinsMixin):

  def test_getSlapOSPendingTicket_support_request(self):
    person = self.makePerson()
    ticket = self.portal.support_request_module.newContent(\
                        title="Test Support Request %s" % self.new_id,
                        destination_decision=person.getRelativeUrl())

    pending_ticket_list = person.Person_getSlapOSPendingTicket()
    # Not indexed yet
    self.assertEqual(len(pending_ticket_list), 0)

    self.tic()

    pending_ticket_list = person.Person_getSlapOSPendingTicket()
    self.assertEqual(len(pending_ticket_list), 0)

    ticket.submit()
    ticket.immediateReindexObject()
    pending_ticket_list = person.Person_getSlapOSPendingTicket()
    self.assertEqual(len(pending_ticket_list), 0)

    ticket.validate()
    ticket.immediateReindexObject()
    pending_ticket_list = person.Person_getSlapOSPendingTicket()
    self.assertEqual(len(pending_ticket_list), 0)

    ticket.suspend()
    ticket.immediateReindexObject()
    pending_ticket_list = person.Person_getSlapOSPendingTicket()
    self.assertEqual(len(pending_ticket_list), 1)
    self.assertEqual(pending_ticket_list[0].getUid(), ticket.getUid())

    ticket.invalidate()
    ticket.immediateReindexObject()
    pending_ticket_list = person.Person_getSlapOSPendingTicket()
    self.assertEqual(len(pending_ticket_list), 0)

  def test_getSlapOSPendingTicket_support_request_cancelled(self):
    person = self.makePerson()
    ticket = self.portal.support_request_module.newContent(\
                        title="Test Support Request %s" % self.new_id,
                        destination_decision=person.getRelativeUrl())

    pending_ticket_list = person.Person_getSlapOSPendingTicket()
    # Not indexed yet
    self.assertEqual(len(pending_ticket_list), 0)

    self.tic()

    pending_ticket_list = person.Person_getSlapOSPendingTicket()
    self.assertEqual(len(pending_ticket_list), 0)

    ticket.submit()
    ticket.immediateReindexObject()
    pending_ticket_list = person.Person_getSlapOSPendingTicket()
    self.assertEqual(len(pending_ticket_list), 0)

    ticket.cancel()
    ticket.immediateReindexObject()
    pending_ticket_list = person.Person_getSlapOSPendingTicket()
    self.assertEqual(len(pending_ticket_list), 0)

  def test_getSlapOSPendingTicket_upgrade_decision(self):
    def newUpgradeDecision():
      ticket = self.portal.upgrade_decision_module.newContent(
        portal_type='Upgrade Decision',
        title="Upgrade Decision Test %s" % self.new_id,
        reference="TESTUD-%s" % self.new_id)

      ticket.immediateReindexObject()
      return ticket

    person = self.makePerson()
    ticket = newUpgradeDecision()
    ticket.setDestinationDecisionValue(person)

    ticket.newContent(
      portal_type="Upgrade Decision Line"
    )
    pending_ticket_list = person.Person_getSlapOSPendingTicket()
    # Not indexed yet
    self.assertEqual(len(pending_ticket_list), 0)

    self.tic()

    pending_ticket_list = person.Person_getSlapOSPendingTicket()
    self.assertEqual(len(pending_ticket_list), 0)

    ticket.plan()
    ticket.immediateReindexObject()
    pending_ticket_list = person.Person_getSlapOSPendingTicket()
    self.assertEqual(len(pending_ticket_list), 0)

    ticket.confirm()
    ticket.immediateReindexObject()
    pending_ticket_list = person.Person_getSlapOSPendingTicket()
    self.assertEqual(len(pending_ticket_list), 1)
    self.assertEqual(pending_ticket_list[0].getUid(), ticket.getUid())

    ticket.start()
    ticket.immediateReindexObject()
    pending_ticket_list = person.Person_getSlapOSPendingTicket()
    self.assertEqual(len(pending_ticket_list), 0)

    ticket.stop()
    ticket.immediateReindexObject()
    pending_ticket_list = person.Person_getSlapOSPendingTicket()
    self.assertEqual(len(pending_ticket_list), 0)

    ticket.deliver()
    ticket.immediateReindexObject()
    pending_ticket_list = person.Person_getSlapOSPendingTicket()
    self.assertEqual(len(pending_ticket_list), 0)


  def test_getSlapOSPendingTicket_upgrade_decision_cancel(self):
    def newUpgradeDecision():
      ticket = self.portal.upgrade_decision_module.newContent(
        portal_type='Upgrade Decision',
        title="Upgrade Decision Test %s" % self.new_id,
        reference="TESTUD-%s" % self.new_id)

      ticket.immediateReindexObject()
      return ticket

    person = self.makePerson()
    ticket = newUpgradeDecision()
    ticket.setDestinationDecisionValue(person)


    ticket.newContent(
      portal_type="Upgrade Decision Line"
    )
    pending_ticket_list = person.Person_getSlapOSPendingTicket()
    # Not indexed yet
    self.assertEqual(len(pending_ticket_list), 0)

    self.tic()

    pending_ticket_list = person.Person_getSlapOSPendingTicket()
    self.assertEqual(len(pending_ticket_list), 0)

    ticket.plan()
    ticket.immediateReindexObject()
    pending_ticket_list = person.Person_getSlapOSPendingTicket()
    self.assertEqual(len(pending_ticket_list), 0)

    ticket.cancel()
    ticket.immediateReindexObject()
    pending_ticket_list = person.Person_getSlapOSPendingTicket()
    self.assertEqual(len(pending_ticket_list), 0)


class TestSlapOSPerson_getSlapOSPendingTicketMessageTemplate(TestCRMSkinsMixin):

  @simulate('NotificationTool_getDocumentValue',
            'reference=None',
  'assert reference == "slapos-crm-person-pending-ticket-notification"\n' \
  'return None')
  @simulate('Person_getSlapOSPendingTicket', '*args, **kwargs','return range(99)')
  def test_getSlapOSPendingTicketMessageTemplate(self):
    person = self.makePerson()
    # Test without notification message
    title, message = person.Person_getSlapOSPendingTicketMessageTemplate()
    self.assertEqual(""" You have 99 pending tickets  """, title)
    self.assertEqual(""" You have 99 pending tickets  """, message)

  def _makeNotificationMessage(self):
    notification_message = self.portal.notification_message_module.newContent(
      portal_type="Notification Message",
      title='Pending ticket',
      text_content_substitution_mapping_method_id='NotificationMessage_getSubstitutionMappingDictFromArgument',
      text_content='Test NM content ${username} AMOUNT (${amount}) WEBSITE(${website})',
      content_type='text/plain',
      )

    return notification_message.getRelativeUrl()

  @simulate('Person_getSlapOSPendingTicket', '*args, **kwargs','return range(99)')
  @simulate('NotificationTool_getDocumentValue',
            'reference=None',
  'assert reference == "slapos-crm-person-pending-ticket-notification"\n' \
  'return context.restrictedTraverse(' \
  'context.REQUEST["test_getSlapOSPendingTicketMessageTemplate"])')
  def test_getSlapOSPendingTicketMessageTemplate_with_notification_message(self):
    person = self.makePerson()

    self.portal.REQUEST['test_getSlapOSPendingTicketMessageTemplate'] = \
        self._makeNotificationMessage()

    title, message = person.Person_getSlapOSPendingTicketMessageTemplate()
    self.assertEqual('Pending ticket', title)
    web_site_url = self.portal.portal_preferences.getPreferredSlaposWebSiteUrl()
    self.assertEqual(message,
      'Test NM content Member Template AMOUNT (99) WEBSITE(%s)' % web_site_url)

class TestSlapOSPerson_sendPendingTicketReminder(TestCRMSkinsMixin):

  @simulate('Person_getSlapOSPendingTicket', '*args, **kwargs','return []')
  @simulate('Person_sendSlapOSPendingTicketNotification', '*args, **kwargs','assert False')
  def test_sendPendingTicketReminder(self):
    person = self.makePerson()
    # Script Person_sendSlapOSPendingTicketNotification not called 
    person.Person_sendPendingTicketReminder()

  @simulate('Person_getSlapOSPendingTicket', '*args, **kwargs','return [1]')
  @simulate('Person_sendSlapOSPendingTicketNotification', '*args, **kwargs',
    'context.REQUEST.set("test_getSlapOSPendingTicketMessageTemplate", "called")')
  def test_sendPendingTicketReminder_positive_amount(self):
    person = self.makePerson()
    person.Person_sendPendingTicketReminder()

    self.assertEqual(self.portal.REQUEST["test_getSlapOSPendingTicketMessageTemplate"],
      "called")

class TestSlapOSPerson_sendSlapOSPendingTicketNotification(TestCRMSkinsMixin):

  def test_sendSlapOSPendingTicketNotification(self):
    person = self.makePerson()
    event = person.Person_sendSlapOSPendingTicketNotification(
      "TEST TITLE",
      "TEST CONTENT",
      batch_mode=1
    )
    self.tic()
    self.assertEqual(event.getTitle(), "TEST TITLE")
    self.assertEqual(event.getTextContent(), "TEST CONTENT")
    self.assertEqual(event.getSimulationState(), "started")
    self.assertEqual(event.getPortalType(), "Mail Message")
    self.assertEqual(event.getDestination(), person.getRelativeUrl())
