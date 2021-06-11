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
from Products.ERP5Type.tests.utils import createZODBPythonScript
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
    self._makeComputer()
    software_installation = self.portal\
       .software_installation_module.template_software_installation\
       .Base_createCloneDocument(batch_mode=1)
    software_installation.edit(
       url_string=self.generateNewSoftwareReleaseUrl(),
       aggregate=self.computer.getRelativeUrl(),
       reference='TESTSOFTINSTS-%s' % self.generateNewId(),
       title='Start requested for %s' % self.computer.getUid()
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

class TestSlapOSFolder_getOpenTicketList(TestCRMSkinsMixin):

  def _test_ticket(self, ticket, expected_amount):
    module = ticket.getParentValue()
    open_ticket_list = module.Folder_getOpenTicketList(title=ticket.getTitle())

    self.assertEqual(len(open_ticket_list), expected_amount-1)

    ticket.submit()
    ticket.immediateReindexObject()
    open_ticket_list = module.Folder_getOpenTicketList(title=ticket.getTitle())
    self.assertEqual(len(open_ticket_list), expected_amount)
    self.assertEqual(open_ticket_list[0].getUid(), ticket.getUid())

    ticket.validate()
    ticket.immediateReindexObject()
    open_ticket_list = module.Folder_getOpenTicketList(title=ticket.getTitle())
    self.assertEqual(len(open_ticket_list), expected_amount)
    self.assertEqual(open_ticket_list[0].getUid(), ticket.getUid())

    ticket.suspend()
    ticket.immediateReindexObject()
    open_ticket_list = module.Folder_getOpenTicketList(title=ticket.getTitle())
    self.assertEqual(len(open_ticket_list), expected_amount)
    self.assertEqual(open_ticket_list[0].getUid(), ticket.getUid())

    ticket.invalidate()
    ticket.immediateReindexObject()
    open_ticket_list = module.Folder_getOpenTicketList(title=ticket.getTitle())
    self.assertEqual(len(open_ticket_list), expected_amount)
    self.assertEqual(open_ticket_list[0].getUid(), ticket.getUid())

  def _test_upgrade_decision(self, ticket, expected_amount):
    module = ticket.getParentValue()
    open_ticket_list = module.Folder_getOpenTicketList(title=ticket.getTitle())

    self.assertEqual(len(open_ticket_list), expected_amount-1)

    ticket.plan()
    ticket.immediateReindexObject()
    open_ticket_list = module.Folder_getOpenTicketList(title=ticket.getTitle())
    self.assertEqual(len(open_ticket_list), expected_amount-1)

    ticket.confirm()
    ticket.immediateReindexObject()
    open_ticket_list = module.Folder_getOpenTicketList(title=ticket.getTitle())
    self.assertEqual(len(open_ticket_list), expected_amount)
    self.assertTrue(ticket.getUid() in [i.getUid() for i in open_ticket_list])

    ticket.start()
    ticket.immediateReindexObject()
    open_ticket_list = module.Folder_getOpenTicketList(title=ticket.getTitle())
    self.assertEqual(len(open_ticket_list), expected_amount-1)


    ticket.stop()
    ticket.immediateReindexObject()
    open_ticket_list = module.Folder_getOpenTicketList(title=ticket.getTitle())
    self.assertEqual(len(open_ticket_list), expected_amount-1)

    ticket.deliver()
    ticket.immediateReindexObject()
    open_ticket_list = module.Folder_getOpenTicketList(title=ticket.getTitle())
    self.assertEqual(len(open_ticket_list), expected_amount)
    self.assertTrue(ticket.getUid() in [i.getUid() for i in open_ticket_list])

  def test_support_request(self):
    def newSupportRequest():
      sr = self.portal.support_request_module.newContent(\
                        title="Test Support Request %s" % self.new_id)

      sr.immediateReindexObject()
      return sr

    ticket = newSupportRequest()
    self._test_ticket(ticket, 1)

    ticket = newSupportRequest()
    self._test_ticket(ticket, 2)

  def test_regularisation_request(self):
    def newRegularisationRequest():
      ticket = self.portal.regularisation_request_module.newContent(
        portal_type='Regularisation Request',
        title="Test Reg. Req.%s" % self.new_id,
        reference="TESTREGREQ-%s" % self.new_id
        )

      ticket.immediateReindexObject()
      return ticket

    ticket = newRegularisationRequest()
    self._test_ticket(ticket, 1)

    ticket = newRegularisationRequest()
    self._test_ticket(ticket, 2)

  def test_upgrade_decision(self):
    def newUpgradeDecision():
      ticket = self.portal.upgrade_decision_module.newContent(
        portal_type='Upgrade Decision',
        title="Upgrade Decision Test %s" % self.new_id,
        reference="TESTUD-%s" % self.new_id)

      ticket.immediateReindexObject()
      return ticket
    ticket = newUpgradeDecision()
    self._test_upgrade_decision(ticket, 1)

    ticket = newUpgradeDecision()
    self._test_upgrade_decision(ticket, 2)


class TestSlapOSBase_getOpenRelatedTicketList(TestCRMSkinsMixin):

  def test_getOpenRelatedTicketList_support_request_related_to_computer(self):
    self._test_getOpenRelatedTicketList_support_request_related(
      self._makeComputer()[0])

  def test_getOpenRelatedTicketList_support_request_related_to_instance_tree(self):
    self._test_getOpenRelatedTicketList_support_request_related(
      self._makeInstanceTree())

  def _test_getOpenRelatedTicketList_support_request_related(self, document):
    ticket = self.portal.support_request_module.newContent(\
                        title="Test Support Request %s" % self.new_id)

    ticket.setAggregateValue(document)
    open_related_ticket_list = document.Base_getOpenRelatedTicketList()
    # Not indexed yet
    self.assertEqual(len(open_related_ticket_list), 0)

    self.tic()

    open_related_ticket_list = document.Base_getOpenRelatedTicketList()
    self.assertEqual(len(open_related_ticket_list), 1)
    self.assertEqual(open_related_ticket_list[0].getUid(), ticket.getUid())

    ticket.submit()
    ticket.immediateReindexObject()
    open_related_ticket_list = document.Base_getOpenRelatedTicketList()
    self.assertEqual(len(open_related_ticket_list), 1)
    self.assertEqual(open_related_ticket_list[0].getUid(), ticket.getUid())

    ticket.validate()
    ticket.immediateReindexObject()
    open_related_ticket_list = document.Base_getOpenRelatedTicketList()
    self.assertEqual(len(open_related_ticket_list), 1)
    self.assertEqual(open_related_ticket_list[0].getUid(), ticket.getUid())

    ticket.suspend()
    ticket.immediateReindexObject()
    open_related_ticket_list = document.Base_getOpenRelatedTicketList()
    self.assertEqual(len(open_related_ticket_list), 1)
    self.assertEqual(open_related_ticket_list[0].getUid(), ticket.getUid())

    ticket.invalidate()
    ticket.immediateReindexObject()
    open_related_ticket_list = document.Base_getOpenRelatedTicketList()
    self.assertEqual(len(open_related_ticket_list), 1)
    self.assertEqual(open_related_ticket_list[0].getUid(), ticket.getUid())

  def test_getOpenRelatedTicketList_cancelled_support_request_related_to_computer(self):
    self._test_getOpenRelatedTicketList_cancelled_support_request_related(
      self._makeComputer()[0])

  def test_getOpenRelatedTicketList_cancelled_support_request_related_to_instance_tree(self):
    self._test_getOpenRelatedTicketList_cancelled_support_request_related(
      self._makeInstanceTree())

  def _test_getOpenRelatedTicketList_cancelled_support_request_related(self, document):
    ticket = self.portal.support_request_module.newContent(\
                        title="Test Support Request %s" % self.new_id)

    ticket.setAggregateValue(document)
    open_related_ticket_list = document.Base_getOpenRelatedTicketList()
    # Not indexed yet
    self.assertEqual(len(open_related_ticket_list), 0)

    self.tic()

    open_related_ticket_list = document.Base_getOpenRelatedTicketList()
    self.assertEqual(len(open_related_ticket_list), 1)
    self.assertEqual(open_related_ticket_list[0].getUid(), ticket.getUid())

    ticket.submit()
    ticket.immediateReindexObject()
    open_related_ticket_list = document.Base_getOpenRelatedTicketList()
    self.assertEqual(len(open_related_ticket_list), 1)
    self.assertEqual(open_related_ticket_list[0].getUid(), ticket.getUid())

    ticket.cancel()
    ticket.immediateReindexObject()
    open_related_ticket_list = document.Base_getOpenRelatedTicketList()
    self.assertEqual(len(open_related_ticket_list), 0)

  def test_getOpenRelatedTicketList_upgrade_decision_related_to_computer(self):
    self._test_getOpenRelatedTicketList_upgrade_decision_related(
      self._makeComputer()[0])

  def test_getOpenRelatedTicketList_upgrade_decision_related_to_instance_tree(self):
    self._test_getOpenRelatedTicketList_upgrade_decision_related(
      self._makeInstanceTree())

  def _test_getOpenRelatedTicketList_upgrade_decision_related(self, document):
    def newUpgradeDecision():
      ticket = self.portal.upgrade_decision_module.newContent(
        portal_type='Upgrade Decision',
        title="Upgrade Decision Test %s" % self.new_id,
        reference="TESTUD-%s" % self.new_id)

      ticket.immediateReindexObject()
      return ticket
    ticket = newUpgradeDecision()

    ticket.newContent(
      portal_type="Upgrade Decision Line"
    ).setAggregateValue(document)
    open_related_ticket_list = document.Base_getOpenRelatedTicketList()
    # Not indexed yet
    self.assertEqual(len(open_related_ticket_list), 0)

    self.tic()

    open_related_ticket_list = document.Base_getOpenRelatedTicketList()
    self.assertEqual(len(open_related_ticket_list), 1)
    self.assertEqual(open_related_ticket_list[0].getUid(), ticket.getUid())

    ticket.plan()
    ticket.immediateReindexObject()
    open_related_ticket_list = document.Base_getOpenRelatedTicketList()
    self.assertEqual(len(open_related_ticket_list), 1)
    self.assertEqual(open_related_ticket_list[0].getUid(), ticket.getUid())

    ticket.confirm()
    ticket.immediateReindexObject()
    open_related_ticket_list = document.Base_getOpenRelatedTicketList()
    self.assertEqual(len(open_related_ticket_list), 1)
    self.assertEqual(open_related_ticket_list[0].getUid(), ticket.getUid())

    ticket.start()
    ticket.immediateReindexObject()
    open_related_ticket_list = document.Base_getOpenRelatedTicketList()
    self.assertEqual(len(open_related_ticket_list), 1)
    self.assertEqual(open_related_ticket_list[0].getUid(), ticket.getUid())

    ticket.stop()
    ticket.immediateReindexObject()
    open_related_ticket_list = document.Base_getOpenRelatedTicketList()
    self.assertEqual(len(open_related_ticket_list), 1)
    self.assertEqual(open_related_ticket_list[0].getUid(), ticket.getUid())

    ticket.deliver()
    ticket.immediateReindexObject()
    open_related_ticket_list = document.Base_getOpenRelatedTicketList()
    self.assertEqual(len(open_related_ticket_list), 1)
    self.assertEqual(open_related_ticket_list[0].getUid(), ticket.getUid())

  def test_getOpenRelatedTicketList_cancelled_upgrade_decision_related_to_computer(self):
    self._test_getOpenRelatedTicketList_cancelled_upgrade_decision_related(
      self._makeComputer()[0])

  def test_getOpenRelatedTicketList_cancelled_upgrade_decision_related_to_instance_tree(self):
    self._test_getOpenRelatedTicketList_cancelled_upgrade_decision_related(
      self._makeInstanceTree())

  def _test_getOpenRelatedTicketList_cancelled_upgrade_decision_related(self, document):
    def newUpgradeDecision():
      ticket = self.portal.upgrade_decision_module.newContent(
        portal_type='Upgrade Decision',
        title="Upgrade Decision Test %s" % self.new_id,
        reference="TESTUD-%s" % self.new_id)

      ticket.immediateReindexObject()
      return ticket
    ticket = newUpgradeDecision()

    ticket.newContent(
      portal_type="Upgrade Decision Line"
    ).setAggregateValue(document)
    open_related_ticket_list = document.Base_getOpenRelatedTicketList()
    # Not indexed yet
    self.assertEqual(len(open_related_ticket_list), 0)

    self.tic()

    open_related_ticket_list = document.Base_getOpenRelatedTicketList()
    self.assertEqual(len(open_related_ticket_list), 1)
    self.assertEqual(open_related_ticket_list[0].getUid(), ticket.getUid())

    ticket.cancel()
    ticket.immediateReindexObject()
    open_related_ticket_list = document.Base_getOpenRelatedTicketList()
    self.assertEqual(len(open_related_ticket_list), 0)

class TestSlapOSTicketEvent(TestCRMSkinsMixin):

  def _test_event(self, ticket):

    def newEvent(ticket):
      event = self.portal.event_module.newContent(
        title="Test Event %s" % self.new_id,
        portal_type="Web Message",
        follow_up_value=ticket)

      event.immediateReindexObject()
      return event

    last_event = ticket.Ticket_getLatestEvent()

    self.assertEqual(last_event, None)

    event = newEvent(ticket)
    last_event = ticket.Ticket_getLatestEvent()

    self.assertEqual(last_event, None)

    event.plan()
    event.immediateReindexObject()
    self.assertEqual(last_event, None)

    event.confirm()
    event.immediateReindexObject()
    last_event = ticket.Ticket_getLatestEvent()
    self.assertEqual(last_event, event)

    event.start()
    event.immediateReindexObject()
    last_event = ticket.Ticket_getLatestEvent()
    self.assertEqual(last_event, event)

    event.stop()
    event.immediateReindexObject()
    last_event = ticket.Ticket_getLatestEvent()
    self.assertEqual(last_event, event)

    event.deliver()
    event.immediateReindexObject()
    last_event = ticket.Ticket_getLatestEvent()
    self.assertEqual(last_event, event)

    # Now we test unwanted cases (deleted and cancelled)
    another_event = newEvent(ticket)
    last_event = ticket.Ticket_getLatestEvent()

    self.assertEqual(last_event, event)

    another_event.cancel()
    event.immediateReindexObject()
    last_event = ticket.Ticket_getLatestEvent()
    self.assertEqual(last_event, event)

    another_event = newEvent(ticket)
    last_event = ticket.Ticket_getLatestEvent()

    self.assertEqual(last_event, event)

    another_event.delete()
    event.immediateReindexObject()
    last_event = ticket.Ticket_getLatestEvent()
    self.assertEqual(last_event, event)

class TestSlapOSEvent_getRSSTextContent(TestSlapOSTicketEvent):

  def test_Event_getRSSTextContent(self):
    source = self.person

    destination = self.portal.person_module.newContent(
      portal_type='Person',
      title="Person Destination %s" % self.new_id,
      reference="TESTPERSD-%s" % self.new_id,
      default_email_text="live_test_%s@example.org" % self.new_id,
      )

    destination_2 = self.portal.person_module.newContent(
      portal_type='Person',
      title="Person Destination 2 %s" % self.new_id,
      reference="TESTPERSD2-%s" % self.new_id,
      default_email_text="live_test_%s@example.org" % self.new_id,
      )

    event = self.portal.event_module.newContent(
        title="Test Event %s" % self.new_id,
        portal_type="Web Message",
        text_content="Test Event %s" % self.new_id)


    text_content = event.Event_getRSSTextContent()

    self.assertTrue(event.getTextContent() in text_content)
    self.assertTrue("Sender: " in text_content, "Sender: not in %s" % text_content)
    self.assertTrue("Recipient: " in text_content, "Recipient: not in %s" % text_content)
    self.assertTrue("Content:" in text_content, "Content: not in %s" % text_content)

    event.setSourceValue(source)
    text_content = event.Event_getRSSTextContent()
    self.assertTrue("Sender: %s" % source.getTitle() in text_content,
      "Sender: %s not in %s" % (source.getTitle(), text_content))

    event.setDestinationValue(destination)
    text_content = event.Event_getRSSTextContent()
    self.assertTrue("Recipient: %s" % destination.getTitle() in text_content,
      "Recipient: %s not in %s" % (destination.getTitle(), text_content))

    event.setDestinationValue(destination_2)
    text_content = event.Event_getRSSTextContent()
    self.assertTrue("Recipient: %s" % destination_2.getTitle() in text_content,
      "Recipient: %s not in %s" % (destination.getTitle(), text_content))

    event.setDestinationValueList([destination, destination_2])
    text_content = event.Event_getRSSTextContent()
    self.assertTrue(
      "Recipient: %s,%s" % (destination.getTitle(),
                            destination_2.getTitle()) in text_content,
      "Recipient: %s,%s not in %s" % (destination.getTitle(),
                                      destination_2.getTitle(),
                                      text_content)
      )

  def test_support_request(self):
    ticket = self.portal.support_request_module.newContent(\
                        title="Test Support Request %s" % self.new_id,
                        resource="service_module/slapos_crm_monitoring",
                        destination_decision_value=self.person)

    ticket.immediateReindexObject()
    self._test_event(ticket)


class TestSlapOSTicket_getLatestEvent(TestSlapOSTicketEvent):

  def test_support_request(self):
    ticket = self.portal.support_request_module.newContent(\
                        title="Test Support Request %s" % self.new_id,
                        resource="service_module/slapos_crm_monitoring",
                        destination_decision_value=self.person)

    ticket.immediateReindexObject()
    self._test_event(ticket)


  def test_regularisation_request(self):
    ticket = self.portal.regularisation_request_module.newContent(
        portal_type='Regularisation Request',
        title="Test Reg. Req.%s" % self.new_id,
        reference="TESTREGREQ-%s" % self.new_id
        )

    ticket.immediateReindexObject()
    self._test_event(ticket)

  def test_upgrade_decision(self):
    ticket = self.portal.upgrade_decision_module.newContent(
        portal_type='Upgrade Decision',
        title="Upgrade Decision Test %s" % self.new_id,
        reference="TESTUD-%s" % self.new_id
        )

    ticket.immediateReindexObject()
    self._test_event(ticket)

class TestSlapOSComputer_notifyWrongAllocationScope(TestCRMSkinsMixin):

  def afterSetUp(self):
    TestCRMSkinsMixin.afterSetUp(self)
    self._cancelTestSupportRequestList(title="%%TESTCOMPT-%")

  def _getGeneratedSupportRequest(self, computer):
    request_title = '%%We have changed allocation scope for %s' % \
                        computer.getReference()
    support_request = self.portal.portal_catalog.getResultValue(
          portal_type = 'Support Request',
          title = request_title,
          simulation_state = 'suspended',
          default_aggregate_uid = computer.getUid()
    )
    return support_request

  def _makeNotificationMessage(self, reference):
    notification_message = self.portal.notification_message_module.newContent(
      portal_type="Notification Message",
      title='We have changed allocation scope for %s' % reference,
      text_content='Test NM content<br/>%s<br/>' % reference,
      content_type='text/html',
      )

    return notification_message.getRelativeUrl()


  @simulate('ERP5Site_isSupportRequestCreationClosed', '*args, **kwargs','return 0')
  @simulate('NotificationTool_getDocumentValue',
            'reference=None',
  'assert reference == "slapos-crm-computer_allocation_scope.notification"\n' \
  'return context.restrictedTraverse(' \
  'context.REQUEST["test_computerNotAllowedAllocationScope_OpenPublic"])')
  @simulate('SupportRequest_trySendNotificationMessage',
            'message_title, message, destination_relative_url',
  'context.portal_workflow.doActionFor(' \
  'context, action="edit_action", ' \
  'comment="Visited by SupportRequest_trySendNotificationMessage ' \
  '%s %s %s" % (message_title, message, destination_relative_url))\n' \
  'return 1')
  def test_computerNotAllowedAllocationScope_OpenPublic(self):
    computer = self._makeComputer(owner=self.makePerson(user=0))[0]
    person = computer.getSourceAdministrationValue()

    self.portal.REQUEST['test_computerNotAllowedAllocationScope_OpenPublic'] = \
        self._makeNotificationMessage(computer.getReference())

    computer.edit(allocation_scope='open/public')
    ticket = computer.Computer_checkAndUpdateAllocationScope()
    self.tic()
    self.assertEqual(computer.getAllocationScope(), 'open/personal')
    #ticket = self._getGeneratedSupportRequest(computer)
    self.assertNotEqual(None, ticket)
    self.assertEqual(ticket.getSimulationState(), 'suspended')

    self.assertEqual('Visited by SupportRequest_trySendNotificationMessage ' \
      '%s %s %s' % \
      ('Allocation scope of %s changed to %s' % (computer.getReference(),
                                                  'open/personal'),
       'Test NM content\n%s\n' % computer.getReference(), person.getRelativeUrl()),
      ticket.workflow_history['edit_workflow'][-1]['comment'])


  @simulate('ERP5Site_isSupportRequestCreationClosed', '*args, **kwargs','return 0')
  @simulate('NotificationTool_getDocumentValue',
            'reference=None',
  'assert reference == "slapos-crm-computer_allocation_scope.notification"\n' \
  'return context.restrictedTraverse(' \
  'context.REQUEST["test_computerNotAllowedAllocationScope_OpenFriend"])')
  @simulate('SupportRequest_trySendNotificationMessage',
            'message_title, message, destination_relative_url',
  'context.portal_workflow.doActionFor(' \
  'context, action="edit_action", ' \
  'comment="Visited by SupportRequest_trySendNotificationMessage ' \
  '%s %s %s" % (message_title, message, destination_relative_url))\n' \
  'return 1')
  def test_computerNotAllowedAllocationScope_OpenFriend(self):
    computer = self._makeComputer(owner=self.makePerson(user=0))[0]
    person = computer.getSourceAdministrationValue()

    self.portal.REQUEST['test_computerNotAllowedAllocationScope_OpenFriend'] = \
        self._makeNotificationMessage(computer.getReference())

    friend_person = self.makePerson()
    computer.edit(allocation_scope='open/friend',
        destination_section=friend_person.getRelativeUrl())
    ticket = computer.Computer_checkAndUpdateAllocationScope()
    self.tic()
    self.assertEqual(computer.getAllocationScope(), 'open/personal')
    self.assertEqual(ticket.getSimulationState(), 'suspended')
    self.assertEqual('Visited by SupportRequest_trySendNotificationMessage ' \
      '%s %s %s' % \
      ('Allocation scope of %s changed to %s' % (computer.getReference(),
                                                  'open/personal'),
       'Test NM content\n%s\n' % computer.getReference(), person.getRelativeUrl()),
      ticket.workflow_history['edit_workflow'][-1]['comment'])

  @simulate('ERP5Site_isSupportRequestCreationClosed', '*args, **kwargs','return 0')
  @simulate('Computer_hasContactedRecently', '*args, **kwargs','return False')
  @simulate('NotificationTool_getDocumentValue',
            'reference=None',
  'assert reference == "slapos-crm-computer-allocation-scope-closed.notification"\n' \
  'return context.restrictedTraverse(' \
  'context.REQUEST["test_computerToCloseAllocationScope_OpenPersonal"])')
  @simulate('SupportRequest_trySendNotificationMessage',
            'message_title, message, destination_relative_url',
  'context.portal_workflow.doActionFor(' \
  'context, action="edit_action", ' \
  'comment="Visited by SupportRequest_trySendNotificationMessage ' \
  '%s %s %s" % (message_title, message, destination_relative_url))\n' \
  'return 1')
  def test_computerToCloseAllocationScope_OpenPersonal(self):
    computer = self._makeComputer(owner=self.makePerson(user=0))[0]
    person = computer.getSourceAdministrationValue()
    target_allocation_scope = 'close/outdated'

    self.portal.REQUEST['test_computerToCloseAllocationScope_OpenPersonal'] = \
        self._makeNotificationMessage(computer.getReference())

    computer.edit(allocation_scope='open/personal')
    support_request = computer.Computer_checkAndUpdatePersonalAllocationScope()
    self.tic()

    self.assertEqual('suspended', support_request.getSimulationState())
    self.assertEqual(computer.getAllocationScope(), target_allocation_scope)
    self.assertEqual('Visited by SupportRequest_trySendNotificationMessage ' \
      '%s %s %s' % \
      ('Allocation scope of %s changed to %s' % (computer.getReference(),
                                                  target_allocation_scope),
       'Test NM content\n%s\n' % computer.getReference(), person.getRelativeUrl()),
      support_request.workflow_history['edit_workflow'][-1]['comment'])

  def test_computerNormalAllocationScope_OpenPersonal(self):
    computer = self._makeComputer(owner=self.makePerson(user=0))[0]
    person = computer.getSourceAdministrationValue()
    self._updatePersonAssignment(person, 'role/service_provider')

    computer.edit(allocation_scope='open/personal')
    computer.Computer_checkAndUpdateAllocationScope()
    self.tic()
    self.assertEqual(computer.getAllocationScope(), 'open/personal')

  def test_computerAllowedAllocationScope_OpenPublic(self):
    computer = self._makeComputer(owner=self.makePerson(user=0))[0]
    person = computer.getSourceAdministrationValue()
    self._updatePersonAssignment(person, 'role/service_provider')

    computer.edit(allocation_scope='open/public')
    computer.Computer_checkAndUpdateAllocationScope()
    self.tic()
    self.assertEqual(computer.getAllocationScope(), 'open/public')

  def test_computerAllowedAllocationScope_OpenFriend(self):
    computer = self._makeComputer(owner=self.makePerson(user=0))[0]
    friend_person = self.makePerson()
    person = computer.getSourceAdministrationValue()
    self._updatePersonAssignment(person, 'role/service_provider')

    computer.edit(allocation_scope='open/friend',
        destination_section=friend_person.getRelativeUrl())
    computer.Computer_checkAndUpdateAllocationScope()
    self.tic()
    self.assertEqual(computer.getAllocationScope(), 'open/friend')


class TestComputer_hasContactedRecently(SlapOSTestCaseMixinWithAbort):

  def createSPL(self, computer):
    delivery_template = self.portal.restrictedTraverse(
      self.portal.portal_preferences.getPreferredInstanceDeliveryTemplate())
    delivery = delivery_template.Base_createCloneDocument(batch_mode=1)

    delivery.edit(
      title="TEST SPL COMP %s" % computer.getReference(),
      start_date=computer.getCreationDate(),
    )

    delivery.newContent(
      portal_type="Sale Packing List Line",
      title="SPL Line for %s" % computer.getReference(),
      quantity=1,
      aggregate_value_list=computer,
    )
    delivery.confirm(comment="Created from %s" % computer.getRelativeUrl())
    delivery.start()
    delivery.stop()
    delivery.deliver()
    return delivery

  def test_Computer_hasContactedRecently_newly_created(self):
    computer = self._makeComputer()[0]
    self.tic()
    has_contacted = computer.Computer_hasContactedRecently()
    self.assertTrue(has_contacted)

  @simulate('Computer_getCreationDate', '*args, **kwargs','return DateTime() - 32')
  def test_Computer_hasContactedRecently_no_data(self):
    computer = self._makeComputer()[0]
    self.tic()

    computer.getCreationDate = self.portal.Computer_getCreationDate
    has_contacted = computer.Computer_hasContactedRecently()
    self.assertFalse(has_contacted)

  @simulate('Computer_getCreationDate', '*args, **kwargs','return DateTime() - 32')
  def test_Computer_hasContactedRecently_memcached(self):
    computer = self._makeComputer()[0]
    memcached_dict = self.portal.portal_memcached.getMemcachedDict(
        key_prefix='slap_tool',
        plugin_path='portal_memcached/default_memcached_plugin')

    memcached_dict[computer.getReference()] = json.dumps({
      "created_at": DateTime().strftime("%Y/%m/%d %H:%M")
    })
    self.tic()

    computer.getCreationDate = self.portal.Computer_getCreationDate

    has_contacted = computer.Computer_hasContactedRecently()
    self.assertTrue(has_contacted)

  @simulate('Computer_getCreationDate', '*args, **kwargs','return DateTime() - 32')
  def test_Computer_hasContactedRecently_memcached_oudated_no_spl(self):
    computer = self._makeComputer()[0]
    memcached_dict = self.portal.portal_memcached.getMemcachedDict(
        key_prefix='slap_tool',
        plugin_path='portal_memcached/default_memcached_plugin')

    memcached_dict[computer.getReference()] = json.dumps({
      "created_at": (DateTime() - 32).strftime("%Y/%m/%d %H:%M")
    })
    self.tic()

    computer.getCreationDate = self.portal.Computer_getCreationDate

    has_contacted = computer.Computer_hasContactedRecently()
    self.assertFalse(has_contacted)

  @simulate('Computer_getCreationDate', '*args, **kwargs','return DateTime() - 32')
  def test_Computer_hasContactedRecently_memcached_oudated_with_spl(self):
    computer = self._makeComputer()[0]
    memcached_dict = self.portal.portal_memcached.getMemcachedDict(
        key_prefix='slap_tool',
        plugin_path='portal_memcached/default_memcached_plugin')

    memcached_dict[computer.getReference()] = json.dumps({
      "created_at": (DateTime() - 32).strftime("%Y/%m/%d %H:%M")
    })
    self.createSPL(computer)
    self.tic()

    computer.getCreationDate = self.portal.Computer_getCreationDate

    has_contacted = computer.Computer_hasContactedRecently()
    self.assertFalse(has_contacted)

class TestSlapOSPerson_isServiceProvider(SlapOSTestCaseMixin):

  abort_transaction = 1

  def test_Person_isServiceProvider(self):
    person = self.portal.person_module.template_member\
         .Base_createCloneDocument(batch_mode=1)
    person.edit(reference='TESTPERSON-%s' % (self.generateNewId(), ))

    self.assertFalse(person.Person_isServiceProvider())
    person.setRole("service_provider")
    self.assertTrue(person.Person_isServiceProvider())

  def test_Person_isServiceProvider_assignment(self):
    person = self.portal.person_module.template_member\
         .Base_createCloneDocument(batch_mode=1)
    person.edit(reference='TESTPERSON-%s' % (self.generateNewId(), ))

    self.assertFalse(person.Person_isServiceProvider())
    assignment = person.newContent(portal_type="Assignment",
                                   role="service_provider")
    self.assertFalse(person.Person_isServiceProvider())
    assignment.open()
    self.assertTrue(person.Person_isServiceProvider())


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


class TestSlapOSGenerateSupportRequestForSlapOS(TestCRMSkinsMixin):

  def afterSetUp(self):
    TestCRMSkinsMixin.afterSetUp(self)
    self.tic()
    self._cancelTestSupportRequestList()

  def test_computer_Base_generateSupportRequestForSlapOS(self):
    self._makeComputer()
    title = "Test Support Request %s" % self.computer.getReference()
    support_request = self.computer.Base_generateSupportRequestForSlapOS(
      title, title, self.computer.getRelativeUrl()
    )
    self.tic()

    self.assertNotEqual(support_request, None)

    self.assertEqual(support_request.getSimulationState(), "validated")
    self.assertEqual(support_request.getRelativeUrl(),
      self.portal.REQUEST.get("support_request_in_progress", None))

    # The support request is added to computer owner.
    self.assertEqual(support_request.getDestinationDecision(),
                      self.computer.getSourceAdministration())
    self.assertEqual(support_request.getTitle(), title)
    self.assertEqual(support_request.getDescription(), title)
    self.assertEqual(support_request.getAggregateValue(),
                      self.computer)

  def test_software_instance_Base_generateSupportRequestForSlapOS(self):
    instance_tree = self._makeInstanceTree()
    self._makeSoftwareInstance(instance_tree,
                               self.generateNewSoftwareReleaseUrl())

    instance = instance_tree.getSuccessorValue()
    title = "Test Support Request %s" % instance.getReference()
    support_request = instance.Base_generateSupportRequestForSlapOS(
      title, title, instance.getRelativeUrl()
    )
    self.tic()

    self.assertNotEqual(support_request, None)

    self.assertEqual(support_request.getSimulationState(), "validated")
    self.assertEqual(support_request.getRelativeUrl(),
      self.portal.REQUEST.get("support_request_in_progress", None))

    # The support request is added to computer owner.
    self.assertEqual(support_request.getDestinationDecision(),
                      instance_tree.getDestinationSection())
    self.assertEqual(support_request.getTitle(), title)
    self.assertEqual(support_request.getDescription(), title)
    self.assertEqual(support_request.getAggregateValue(),
                      instance)

  def test_instance_tree_Base_generateSupportRequestForSlapOS(self):
    instance_tree = self._makeInstanceTree()

    title = "Test Support Request %s" % instance_tree.getReference()
    support_request = instance_tree.Base_generateSupportRequestForSlapOS(
      title, title, instance_tree.getRelativeUrl()
    )
    self.tic()

    self.assertNotEqual(support_request, None)

    self.assertEqual(support_request.getSimulationState(), "validated")
    self.assertEqual(support_request.getRelativeUrl(),
      self.portal.REQUEST.get("support_request_in_progress", None))

    # The support request is added to computer owner.
    self.assertEqual(support_request.getDestinationDecision(),
                      instance_tree.getDestinationSection())

    self.assertEqual(support_request.getTitle(), title)
    self.assertEqual(support_request.getDescription(), title)
    self.assertEqual(support_request.getAggregateValue(),
                      instance_tree)

  def test_software_installation_Base_generateSupportRequestForSlapOS(self):
    software_installation = self._makeSoftwareInstallation()

    title = "Test Support Request %s" % software_installation.generateNewId()
    support_request = software_installation.Base_generateSupportRequestForSlapOS(
      title, title, software_installation.getRelativeUrl()
    )
    self.tic()

    self.assertNotEqual(support_request, None)

    self.assertEqual(support_request.getSimulationState(), "validated")
    self.assertEqual(support_request.getRelativeUrl(),
      self.portal.REQUEST.get("support_request_in_progress", None))

    # The support request is added to computer owner.
    self.assertEqual(support_request.getDestinationDecision(),
                      software_installation.getDestinationSection())

    self.assertEqual(support_request.getTitle(), title)
    self.assertEqual(support_request.getDescription(), title)
    self.assertEqual(support_request.getAggregateValue(),
                      software_installation)


  def test_Base_generateSupportRequestForSlapOS_do_not_recreate_if_open(self):
    self._makeComputer(owner=self.makePerson(user=0))
    title = "Test Support Request %s" % self.computer.getReference()
    support_request = self.computer.Base_generateSupportRequestForSlapOS(
      title, title, self.computer.getRelativeUrl()
    )
    self.tic()
    self.portal.REQUEST.set("support_request_in_progress", None)

    same_support_request = self.computer.Base_generateSupportRequestForSlapOS(
      title, title, self.computer.getRelativeUrl()
    )

    self.assertEqual(support_request, same_support_request)


  def test_Base_generateSupportRequestForSlapOS_do_not_recreate_if_suspended(self):
    self._makeComputer(owner=self.makePerson(user=0))
    title = "Test Support Request %s" % self.computer.getReference()
    support_request = self.computer.Base_generateSupportRequestForSlapOS(
      title, title, self.computer.getRelativeUrl()
    )

    support_request.suspend()
    self.tic()
    self.portal.REQUEST.set("support_request_in_progress", None)

    same_support_request = self.computer.Base_generateSupportRequestForSlapOS(
      title, title, self.computer.getRelativeUrl()
    )

    self.assertEqual(support_request, same_support_request)

  def test_Base_generateSupportRequestForSlapOS_recreate_if_closed(self):
    self._makeComputer(owner=self.makePerson(user=0))
    title = "Test Support Request %s" % self.computer.getReference()
    support_request = self.computer.Base_generateSupportRequestForSlapOS(
      title, title, self.computer.getRelativeUrl())
    self.tic()

    support_request.invalidate()
    self.tic()

    self.portal.REQUEST.set("support_request_in_progress", None)

    support_request = self.computer.Base_generateSupportRequestForSlapOS(
      title, title, self.computer.getRelativeUrl()
    )
    self.tic()

    self.assertNotEqual(support_request, None)

  def test_Base_generateSupportRequestForSlapOS_recreate(self):
    self._makeComputer(owner=self.makePerson(user=0))
    title = "Test Support Request %s" % self.computer.getRelativeUrl()
    support_request = self.computer.Base_generateSupportRequestForSlapOS(
      title, title, self.computer.getRelativeUrl())

    same_support_request = self.computer.Base_generateSupportRequestForSlapOS(
      title, title, self.computer.getRelativeUrl()
    )

    self.assertEqual(support_request, same_support_request)

  def test_Base_generateSupportRequestForSlapOS_inprogress(self):
    self._makeComputer(owner=self.makePerson(user=0))
    title = "Test Support Request %s" % self.computer.getRelativeUrl()
    support_request = self.computer.Base_generateSupportRequestForSlapOS(
      title, title, self.computer.getRelativeUrl())

    in_progress = support_request.getRelativeUrl()
    self.portal.REQUEST.set("support_request_in_progress", in_progress)

    title = "Test Support Request %s" % self.computer.getRelativeUrl()
    support_request = self.computer.Base_generateSupportRequestForSlapOS(
      title, title, self.computer.getRelativeUrl())

    self.assertEqual(support_request.getRelativeUrl(), in_progress)

class TestSlapOSComputer_CheckState(TestCRMSkinsMixin):

  def beforeTearDown(self):
    self._cancelTestSupportRequestList()
    transaction.abort()

  def afterSetUp(self):
    TestCRMSkinsMixin.afterSetUp(self)
    self._cancelTestSupportRequestList("% TESTCOMPT-%")

  def _makeSupportRequest(self):
    return self.portal.restrictedTraverse(
        self.portal.portal_preferences.getPreferredSupportRequestTemplate()).\
       Base_createCloneDocument(batch_mode=1)

  def _makeNotificationMessage(self, reference):
    notification_message = self.portal.notification_message_module.newContent(
      portal_type="Notification Message",
      title='The Computer %s has not contacted the server for more than 24 hours' % reference,
      text_content='Test NM content<br/>%s<br/>' % reference,
      content_type='text/html',
      )

    return notification_message.getRelativeUrl()

  def _getGeneratedSupportRequest(self, computer_uid, request_title):
    support_request = self.portal.portal_catalog.getResultValue(
          portal_type = 'Support Request',
          title = request_title,
          simulation_state = 'validated',
          default_aggregate_uid = computer_uid
    )
    return support_request

  def _simulateBase_generateSupportRequestForSlapOS(self):
    script_name = 'Base_generateSupportRequestForSlapOS'
    if script_name in self.portal.portal_skins.custom.objectIds():
      raise ValueError('Precondition failed: %s exists in custom' % script_name)
    createZODBPythonScript(self.portal.portal_skins.custom,
      script_name,
      '*args, **kw',
      '# Script body\n'
"""return context.getPortalObject().REQUEST['_simulateBase_generateSupportRequestForSlapOS']""")
    transaction.commit()

  @simulate('ERP5Site_isSupportRequestCreationClosed', '*args, **kwargs','return 0')
  def test_Computer_checkState_call_support_request(self):
    computer = self._makeComputer(owner=self.makePerson(user=0))[0]
    memcached_dict = self.portal.portal_memcached.getMemcachedDict(
      key_prefix='slap_tool',
      plugin_path='portal_memcached/default_memcached_plugin')

    memcached_dict[computer.getReference()] = json.dumps(
        {"created_at":"%s" % (DateTime() - 1.1)}
    )

    self._simulateBase_generateSupportRequestForSlapOS()
    support_request = self._makeSupportRequest()
    self.portal.REQUEST.set('_simulateBase_generateSupportRequestForSlapOS',
                               support_request)

    try:
      computer_support_request = computer.Computer_checkState()
    finally:
      self._dropScript("Base_generateSupportRequestForSlapOS")

    self.assertEqual(support_request,
      computer_support_request)


  @simulate('ERP5Site_isSupportRequestCreationClosed', '*args, **kwargs','return 0')
  def test_Computer_checkState_empty_cache(self):
    computer = self._makeComputer(owner=self.makePerson(user=0))[0]

    self._simulateBase_generateSupportRequestForSlapOS()
    support_request = self._makeSupportRequest()
    self.portal.REQUEST.set('_simulateBase_generateSupportRequestForSlapOS',
                               support_request)

    try:
      computer_support_request = computer.Computer_checkState()
    finally:
      self._dropScript("Base_generateSupportRequestForSlapOS")

    self.assertEqual(support_request,
      computer_support_request)

  @simulate('ERP5Site_isSupportRequestCreationClosed', '*args, **kwargs','return 0')
  @simulate('NotificationTool_getDocumentValue',
            'reference=None',
  'assert reference == "slapos-crm-computer_check_state.notification"\n' \
  'return context.restrictedTraverse(' \
  'context.REQUEST["test_Computer_checkState_notify"])')
  @simulate('SupportRequest_trySendNotificationMessage',
            'message_title, message, destination_relative_url',
  'context.portal_workflow.doActionFor(' \
  'context, action="edit_action", ' \
  'comment="Visited by SupportRequest_trySendNotificationMessage ' \
  '%s %s %s" % (message_title, message, destination_relative_url))')
  def test_Computer_checkState_notify(self):
    computer = self._makeComputer(owner=self.makePerson(user=0))[0]
    person = computer.getSourceAdministrationValue()


    memcached_dict = self.portal.portal_memcached.getMemcachedDict(
      key_prefix='slap_tool',
      plugin_path='portal_memcached/default_memcached_plugin')

    memcached_dict[computer.getReference()] = json.dumps(
        {"created_at":"%s" % (DateTime() - 0.1)}
    )

    self.portal.REQUEST['test_Computer_checkState_notify'] = \
        self._makeNotificationMessage(computer.getReference())

    computer.Computer_checkState()
    self.tic()

    ticket_title = "[MONITORING] Lost contact with computer %s" % computer.getReference()
    ticket = self._getGeneratedSupportRequest(computer.getUid(), ticket_title)
    self.assertNotEqual(ticket, None)
    self.assertEqual('Visited by SupportRequest_trySendNotificationMessage ' \
      '%s %s %s' % ( \
      ticket_title,
      'Test NM content\n%s\n' % computer.getReference(),
      person.getRelativeUrl()),
      ticket.workflow_history['edit_workflow'][-1]['comment'])


  @simulate('ERP5Site_isSupportRequestCreationClosed', '*args, **kwargs','return 0')
  @simulate('NotificationTool_getDocumentValue',
            'reference=None',
  'assert reference == "slapos-crm-computer_check_state.notification"\n' \
  'return context.restrictedTraverse(' \
  'context.REQUEST["test_Computer_checkState_empty_cache_notify"])')
  @simulate('SupportRequest_trySendNotificationMessage',
            'message_title, message, destination_relative_url',
  'context.portal_workflow.doActionFor(' \
  'context, action="edit_action", ' \
  'comment="Visited by SupportRequest_trySendNotificationMessage ' \
  '%s %s %s" % (message_title, message, destination_relative_url))')
  def test_Computer_checkState_empty_cache_notify(self):
    computer = self._makeComputer(owner=self.makePerson(user=0))[0]
    person = computer.getSourceAdministrationValue()

    self.portal.REQUEST['test_Computer_checkState_empty_cache_notify'] = \
        self._makeNotificationMessage(computer.getReference())

    computer.Computer_checkState()
    self.tic()

    ticket_title = "[MONITORING] Lost contact with computer %s" % computer.getReference()
    ticket = self._getGeneratedSupportRequest(computer.getUid(), ticket_title)
    self.assertNotEqual(ticket, None)
    self.assertEqual('Visited by SupportRequest_trySendNotificationMessage ' \
      '%s %s %s' % ( \
      ticket_title,
      'Test NM content\n%s\n' % computer.getReference(),
      person.getRelativeUrl()),
      ticket.workflow_history['edit_workflow'][-1]['comment'])


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
  @simulate('SupportRequest_trySendNotificationMessage',
            'message_title, message, destination_relative_url',
  'context.portal_workflow.doActionFor(' \
  'context, action="edit_action", ' \
  'comment="Visited by SupportRequest_trySendNotificationMessage ' \
  '%s %s %s" % (message_title, message, destination_relative_url))')
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
    self.assertEqual('Visited by SupportRequest_trySendNotificationMessage ' \
      '%s %s %s' % ( \
      ticket_title,
      'Test NM content\n%s\n' % instance_tree.getReference(),
      person.getRelativeUrl()),
      ticket.workflow_history['edit_workflow'][-1]['comment'])

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
       aggregate=self.computer.getRelativeUrl(),
       reference='TESTSOFTINSTS-%s' % new_id,
       title='Start requested for %s' % self.computer.getUid()
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
        title= "Test hosting sub ticket %s" % new_id,
        reference="TESTHST-%s" % new_id,
        destination_section_value=person
    )

    return instance_tree

  def _makeComputerPartitionList(self):
    for i in range(1, 5):
      id_ = 'partition%s' % (i, )
      p = self.computer.newContent(portal_type='Computer Partition',
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

    self._makeComputer()
    self._makeComputerPartitionList()

    memcached_dict = self.portal.portal_memcached.getMemcachedDict(
      key_prefix='slap_tool',
      plugin_path='portal_memcached/default_memcached_plugin')

    error_date = DateTime()
    memcached_dict[instance.getReference()] = json.dumps(
        {"created_at":"%s" % error_date, "text": "#error "}
    )

    self.assertEqual(instance.SoftwareInstance_hasReportedError(), None)

    instance.setAggregateValue(self.computer.partition1)

    self.assertEqual(str(instance.SoftwareInstance_hasReportedError()), '#error ')

    memcached_dict[instance.getReference()] = json.dumps(
        {"created_at":"%s" % error_date, "text": "#access "}
    )

    self.assertEqual(instance.SoftwareInstance_hasReportedError(), None)

  def test_SoftwareInstallation_hasReportedError(self):
    software_release = self._makeSoftwareRelease()
    self._makeComputer()
    installation = self._makeSoftwareInstallation(
      software_release.getUrlString()
    )

    memcached_dict = self.portal.portal_memcached.getMemcachedDict(
      key_prefix='slap_tool',
      plugin_path='portal_memcached/default_memcached_plugin')

    self.assertEqual(installation.SoftwareInstallation_hasReportedError(), None)

    error_date = DateTime()
    memcached_dict[installation.getReference()] = json.dumps(
        {"created_at":"%s" % error_date, "text": "#error "}
    )

    self.assertEqual(installation.SoftwareInstallation_hasReportedError(), error_date)

    memcached_dict[installation.getReference()] = json.dumps(
        {"created_at":"%s" % error_date, "text": "#building "}
     )

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

      self._makeComputer()
      self._makeComputerPartitionList()
      instance.setAggregateValue(self.computer.partition1)

      memcached_dict = self.portal.portal_memcached.getMemcachedDict(
        key_prefix='slap_tool',
        plugin_path='portal_memcached/default_memcached_plugin')

      error_date = DateTime()
      memcached_dict[instance.getReference()] = json.dumps(
        {"created_at":"%s" % error_date, "text": "#error ", "since": "%s" % (error_date - 2)}
      )

      self.assertEqual(
        'Visited by InstanceTree_createSupportRequestEvent %s %s' % \
        (instance.getUid(),
         "slapos-crm-instance-tree-instance-state.notification"),
        instance_tree.InstanceTree_checkSoftwareInstanceState())

      memcached_dict[instance.getReference()] = json.dumps(
          {"created_at":"%s" % error_date, "text": "#access "}
      )

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

      self._makeComputer()
      self._makeComputerPartitionList()
      instance.setAggregateValue(self.computer.partition1)

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

      self._makeComputer()
      self._makeComputerPartitionList()
      instance.setAggregateValue(self.computer.partition1)

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

      memcached_dict = self.portal.portal_memcached.getMemcachedDict(
        key_prefix='slap_tool',
        plugin_path='portal_memcached/default_memcached_plugin')
      error_date = DateTime()
      memcached_dict[instance.getReference()] = json.dumps(
        {"created_at":"%s" % error_date, "text": "#access "}
      )

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


    self._makeComputer()
    self._makeComputerPartitionList()
    instance.setAggregateValue(self.computer.partition1)

    memcached_dict = self.portal.portal_memcached.getMemcachedDict(
      key_prefix='slap_tool',
      plugin_path='portal_memcached/default_memcached_plugin')

    error_date = DateTime()
    memcached_dict[instance.getReference()] = json.dumps(
      {"created_at":"%s" % error_date, "text": "#error "}
    )

    self.assertEqual(
        None,
        instance_tree.InstanceTree_checkSoftwareInstanceState())

class TestSupportRequestTrySendNotificationMessage(SlapOSTestCaseMixin):

  def test_SupportRequest_trySendNotificationMessage(self):
    self._makeComputer(owner=self.makePerson(user=0))
    person = self.computer.getSourceAdministrationValue()
    title = "Test Support Request %s" % self.computer.getReference()
    text_content='Test NM content<br/>%s<br/>' % self.computer.getReference()

    support_request = self.portal.support_request_module.newContent(\
            title=title, description=title,
            destination_decision=self.computer.getSourceAdministration(),
            aggregate_value=self.computer.getRelativeUrl())
    support_request.validate()
    self.tic()

    first_event = support_request.SupportRequest_trySendNotificationMessage(
      message_title=title, message=text_content,
      destination_relative_url=person.getRelativeUrl()
    )
    self.assertNotEqual(first_event, None)

    self.tic()
    self.assertEqual(
      support_request.getFollowUpRelatedList(),
      [first_event.getRelativeUrl()])

    self.assertEqual(title, first_event.getTitle())
    self.assertEqual(text_content, first_event.getTextContent())
    self.assertNotEqual(None, first_event.getStartDate())
    self.assertEqual("service_module/slapos_crm_information",
                      first_event.getResource())
    self.assertEqual(first_event.getDestination(), person.getRelativeUrl())
    self.assertEqual(first_event.getFollowUp(), support_request.getRelativeUrl())

    event = support_request.SupportRequest_trySendNotificationMessage(
      message_title=title, message=text_content,
      destination_relative_url=person.getRelativeUrl()
    )
    self.assertEqual(event, first_event)

    self.assertEqual(title, event.getTitle())
    self.assertEqual(text_content, event.getTextContent())
    self.assertNotEqual(None, event.getStartDate())
    self.assertEqual("service_module/slapos_crm_information",
                      event.getResource())
    self.assertEqual(event.getDestination(), person.getRelativeUrl())

    title += "__zz"
    event = support_request.SupportRequest_trySendNotificationMessage(
      message_title=title, message=text_content,
      destination_relative_url=person.getRelativeUrl(),
    )

    self.assertEqual(event.getTitle(), title)
    self.assertEqual(text_content, event.getTextContent())
    self.assertNotEqual(None, event.getStartDate())
    self.assertEqual("service_module/slapos_crm_information",
                      event.getResource())
    self.assertEqual(event.getDestination(), person.getRelativeUrl())

    another_support_request = self.portal.support_request_module.newContent(\
            title=title, description=title,
            destination_decision=self.computer.getSourceAdministration(),
            aggregate_value=self.computer.getRelativeUrl())
    another_support_request.validate()
    self.tic()

    another_first_event = \
      another_support_request.SupportRequest_trySendNotificationMessage(
        message_title=title, message=text_content,
        destination_relative_url=person.getRelativeUrl())

    self.assertNotEqual(another_first_event, None)

    self.tic()
    self.assertEqual(
      another_support_request.getFollowUpRelatedList(),
      [another_first_event.getRelativeUrl()])

    self.assertEqual(title, another_first_event.getTitle())
    self.assertEqual(text_content, another_first_event.getTextContent())
    self.assertNotEqual(None, another_first_event.getStartDate())
    self.assertEqual("service_module/slapos_crm_information",
                      another_first_event.getResource())
    self.assertEqual(another_first_event.getDestination(), person.getRelativeUrl())
    self.assertEqual(another_first_event.getFollowUp(),
     another_support_request.getRelativeUrl())


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
        title= "Test hosting sub ticket %s" % new_id,
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
  @simulate('SupportRequest_trySendNotificationMessage',
            "message_title, message, source_relative_url",
     """assert "destroyed" in message
return "Visited by SupportRequest_trySendNotificationMessage %s %s" % (message_title, source_relative_url)""")
  def testSupportRequest_updateMonitoringDestroyRequestedState(self):
    support_request = self._makeSupportRequest()
    self.assertEqual(None,
      support_request.SupportRequest_updateMonitoringDestroyRequestedState())
    support_request.validate()
    self.assertEqual(None,
      support_request.SupportRequest_updateMonitoringDestroyRequestedState())

    support_request.setAggregateValue(
      self._makeComputer(owner=self.makePerson(user=0))[0])
    self.assertEqual(None,
      support_request.SupportRequest_updateMonitoringDestroyRequestedState())

    hs = self._makeInstanceTree()
    support_request.setAggregateValue(hs)

    hs.getSlapState = getFakeSlapState
    self.commit()

    support_request.setDestinationDecisionValue(self.makePerson(user=0))
    expected_text = """Visited by SupportRequest_trySendNotificationMessage Instance Tree was destroyed was destroyed by the user %s""" % support_request.getDestinationDecision()
    self.assertEqual(expected_text,
      support_request.SupportRequest_updateMonitoringDestroyRequestedState())

    self.assertEqual("invalidated",
      support_request.getSimulationState())


