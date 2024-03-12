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
from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixinWithAbort, TemporaryAlarmScript

from DateTime import DateTime
import feedparser
from time import sleep

def getFakeSlapState():
  return "destroy_requested"

class TestRSSSyleSkinsMixin(SlapOSTestCaseMixinWithAbort):

  def afterSetUp(self):
    SlapOSTestCaseMixinWithAbort.afterSetUp(self)
    self.person = self.makePerson(self.addProject(), new_id=self.new_id, index=0, user=0)
    self.clearCache()

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
        follow_up_value=self.addProject()
    )
    return instance_tree

  def newUpgradeDecision(self, person, project, item):
    self.portal.portal_skins.changeSkin('View')
    destination_decision_value = None
    if person is None:
      destination_decision_value = self.makePerson(self.addProject())
    else:
      destination_decision_value = person
    ticket = self.portal.upgrade_decision_module.newContent(
      portal_type='Upgrade Decision',
      title="Upgrade Decision Test %s" % self.new_id,
      reference="TESTUD-%s" % self.new_id,
      destination_value=destination_decision_value,
      destination_decision_value=destination_decision_value,
      destination_project_value=project,
      aggregate_value=item,
      causality_value=item
    )

    ticket.Ticket_createProjectEvent(
      ticket.getTitle(), 'outgoing', 'Web Message',
      'service_module/slapos_crm_monitoring',
      text_content=ticket.getTitle(),
      content_type='text/plain'
    )
    self.tic()
    self.portal.portal_skins.changeSkin('RSS')
    return ticket

  def newRegularisationRequest(self, person):
    self.portal.portal_skins.changeSkin('View')
    ticket = self.portal.regularisation_request_module.newContent(
      portal_type='Regularisation Request',
      title="Test Reg. Req.%s" % self.new_id,
      reference="TESTREGREQ-%s" % self.new_id,
      destination_value=person,
      destination_decision_value=person
     )

    ticket.Ticket_createProjectEvent(
      ticket.getTitle(), 'outgoing', 'Web Message',
      'service_module/slapos_crm_monitoring',
      text_content=ticket.getTitle(),
      content_type='text/plain'
    )
    ticket.submit()
    self.tic()
    self.portal.portal_skins.changeSkin('RSS')
    return ticket

  def newSupportRequest(self, person, causality_value):
    self.portal.portal_skins.changeSkin('View')

    support_request = person.Entity_createTicketFromTradeCondition(
      'service_module/slapos_crm_monitoring',
      "Test Support Request %s" % self.new_id,
      '',
      causality=causality_value.getRelativeUrl(),
      source_project=causality_value.getFollowUp()
    )
    support_request.Ticket_createProjectEvent(
      support_request.getTitle(), 'incoming', 'Web Message',
      support_request.getResource(),
      text_content="Test Support Request %s" % self.new_id,
      content_type='text/plain',
      source=person.getRelativeUrl()
    )
    self.tic()
    return support_request


class TestSlapOSSupportRequestRSS(TestRSSSyleSkinsMixin):

  def test_WebSection_viewTicketListAsRSS(self):
    person = self.makePerson(self.addProject())

    support_request = person.Entity_createTicketFromTradeCondition(
      'service_module/slapos_crm_monitoring',
      'Help',
      'I need help !',
    )
    support_request.Ticket_createProjectEvent(
      support_request.getTitle(), 'incoming', 'Web Message',
      support_request.getResource(),
      text_content=support_request.getDescription(),
      content_type='text/plain',
      source=person.getRelativeUrl()
    )
    self.tic()

    self.login(person.getUserId())
    self.portal.portal_skins.changeSkin('RSS')
    parsed = feedparser.parse(self.portal.WebSection_viewTicketListAsRSS())
    self.assertFalse(parsed.bozo)
    first_entry_id = [item.id for item in parsed.entries]
    self.assertEqual([item.summary for item in parsed.entries], ['I need help !'])

    self.logout()
    sleep(2)
    self.login()
    support_request.Ticket_createProjectEvent(
      support_request.getTitle(), 'outgoing', 'Web Message',
      support_request.getResource(),
      text_content='How can I help you ?',
      content_type='text/plain'
    )
    self.tic()

    self.logout()
    self.login(person.getUserId())
    self.portal.portal_skins.changeSkin('RSS')
    parsed = feedparser.parse(self.portal.WebSection_viewTicketListAsRSS())
    self.assertFalse(parsed.bozo)
    self.assertEqual([item.summary for item in parsed.entries],
      ['How can I help you ?', 'I need help !'])
    self.assertNotEqual([item.id for item in parsed.entries][0], first_entry_id)

  def test_WebSection_viewCriticalTicketListAsRSS(self):
    person = self.makePerson(self.addProject())

    support_request = person.Entity_createTicketFromTradeCondition(
      'service_module/slapos_crm_monitoring',
      'Help',
      'I need help !',
    )
    support_request.Ticket_createProjectEvent(
      support_request.getTitle(), 'incoming', 'Web Message',
      support_request.getResource(),
      text_content=support_request.getDescription(),
      content_type='text/plain',
      source=person.getRelativeUrl()
    )
    self.tic()

    self.login(person.getUserId())
    self.portal.portal_skins.changeSkin('RSS')
    self.clearCache()
    transaction.commit()
    parsed = feedparser.parse(self.portal.WebSection_viewCriticalTicketListAsRSS())
    self.assertFalse(parsed.bozo)
    first_entry_id = [item.id for item in parsed.entries]
    self.assertEqual(len(parsed.entries), 1)
    self.assertEqual([item.summary for item in parsed.entries], ['I need help !'])

    self.logout()
    sleep(2)
    self.login()
    support_request.Ticket_createProjectEvent(
      support_request.getTitle(), 'outgoing', 'Web Message',
      support_request.getResource(),
      text_content='How can I help you ?',
      content_type='text/plain'
    )
    self.tic()

    self.logout()
    self.login(person.getUserId())
    self.portal.portal_skins.changeSkin('RSS')
    parsed = feedparser.parse(self.portal.WebSection_viewCriticalTicketListAsRSS())
    self.assertFalse(parsed.bozo)
    self.assertEqual([item.summary for item in parsed.entries],
      ['How can I help you ?', 'I need help !'])
    self.assertNotEqual([item.id for item in parsed.entries][0], first_entry_id)

class TestSlapOSFolder_getOpenTicketList(TestRSSSyleSkinsMixin):

  def _test_ticket(self, ticket, expected_amount):
    event = ticket.getFollowUpRelatedValue()
    self.assertNotEqual(event, None)
    module = ticket.getParentValue()

    self.portal.portal_skins.changeSkin('RSS')
    open_ticket_list = module.Folder_getOpenTicketList()
    self.assertEqual(len(open_ticket_list), expected_amount)
    self.assertNotEqual(open_ticket_list[0].pubDate, None)
    self.assertEqual(open_ticket_list[0].guid,
      '{}-{}'.format(event.getFollowUp(),
                     event.getRelativeUrl()))

    ticket.validate()
    self.tic()
    self.portal.portal_skins.changeSkin('RSS')
    open_ticket_list = module.Folder_getOpenTicketList()
    self.assertEqual(len(open_ticket_list), expected_amount)
    self.assertNotEqual(open_ticket_list[0].pubDate, None)
    self.assertEqual(open_ticket_list[0].guid,
      '{}-{}'.format(event.getFollowUp(),
                     event.getRelativeUrl()))

    ticket.suspend()
    self.tic()
    self.portal.portal_skins.changeSkin('RSS')
    open_ticket_list = module.Folder_getOpenTicketList()
    self.assertEqual(len(open_ticket_list), expected_amount)
    self.assertNotEqual(open_ticket_list[0].pubDate, None)
    self.assertEqual(open_ticket_list[0].guid,
      '{}-{}'.format(event.getFollowUp(),
                     event.getRelativeUrl()))

    ticket.invalidate()
    self.tic()
    self.portal.portal_skins.changeSkin('RSS')
    open_ticket_list = module.Folder_getOpenTicketList()
    self.assertEqual(len(open_ticket_list), expected_amount)
    # Extra checks
    self.assertNotEqual(open_ticket_list[0].pubDate, None)
    self.assertNotEqual(open_ticket_list[0].link, None)
    self.assertIn(event.getTextContent(), open_ticket_list[0].description)
    self.assertEqual(open_ticket_list[0].guid,
      '{}-{}'.format(event.getFollowUp(),
                     event.getRelativeUrl()))
    self.assertEqual(open_ticket_list[0].title,
      ticket.getTitle())

  def _test_upgrade_decision(self, ticket, expected_amount):
    event = ticket.getFollowUpRelatedValue()
    self.assertNotEqual(event, None)
    module = ticket.getParentValue()
    self.portal.portal_skins.changeSkin('RSS')
    open_ticket_list = module.Folder_getOpenTicketList()
    self.assertEqual(len(open_ticket_list), expected_amount-1)

    ticket.plan()
    self.tic()
    self.portal.portal_skins.changeSkin('RSS')
    open_ticket_list = module.Folder_getOpenTicketList()
    self.assertEqual(len(open_ticket_list), expected_amount-1)

    ticket.confirm()
    self.tic()
    self.portal.portal_skins.changeSkin('RSS')
    open_ticket_list = module.Folder_getOpenTicketList()
    self.assertEqual(len(open_ticket_list), expected_amount)

    self.assertNotEqual(open_ticket_list[0].pubDate, None)
    self.assertEqual(open_ticket_list[0].guid,
      '{}-{}'.format(event.getFollowUp(),
                     event.getRelativeUrl()))

    ticket.start()
    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm',
                              "'disabled'", attribute='comment'):
      self.tic()
    self.portal.portal_skins.changeSkin('RSS')
    open_ticket_list = module.Folder_getOpenTicketList()
    self.assertEqual(len(open_ticket_list), expected_amount)
    self.assertNotEqual(open_ticket_list[0].pubDate, None)
    self.assertEqual(open_ticket_list[0].guid,
      '{}-{}'.format(event.getFollowUp(),
                     event.getRelativeUrl()))

    ticket.stop()
    self.tic()
    self.portal.portal_skins.changeSkin('RSS')
    open_ticket_list = module.Folder_getOpenTicketList()
    self.assertEqual(len(open_ticket_list), expected_amount)
    self.assertNotEqual(open_ticket_list[0].pubDate, None)
    self.assertEqual(open_ticket_list[0].guid,
      '{}-{}'.format(event.getFollowUp(),
                     event.getRelativeUrl()))

    ticket.deliver()
    self.tic()
    self.portal.portal_skins.changeSkin('RSS')
    open_ticket_list = module.Folder_getOpenTicketList()
    self.assertEqual(len(open_ticket_list), expected_amount)
    self.assertNotEqual(open_ticket_list[0].pubDate, None)
    self.assertEqual(open_ticket_list[0].guid,
      '{}-{}'.format(event.getFollowUp(),
                     event.getRelativeUrl()))

  def test_support_request(self):
    instance_tree = self._makeInstanceTree()
    project = instance_tree.getFollowUpValue()
    person = self.makePerson(project, index=1, user=1)
    self.addProjectProductionManagerAssignment(person, project)
    customer = self.makePerson(project)
    self.tic()

    self.portal.portal_skins.changeSkin('RSS')
    self.login(person.getUserId())

    initial_amount = len(
      self.portal.support_request_module.Folder_getOpenTicketList())

    self.login()
    ticket = self.newSupportRequest(customer, instance_tree)
    self.login(person.getUserId())
    self._test_ticket(ticket, initial_amount + 1)

    self.login()
    ticket = self.newSupportRequest(customer, instance_tree)
    self.login(person.getUserId())
    self._test_ticket(ticket, initial_amount + 2)

  def test_regularisation_request(self):

    project = self.addProject()
    person = self.makePerson(project, index=1, user=1)
    self.addSaleManagerAssignment(person)
    customer = self.makePerson(project, index=1, user=1)
    self.tic()

    self.portal.portal_skins.changeSkin('RSS')
    self.login(person.getUserId())

    initial_amount = len(
      self.portal.regularisation_request_module.Folder_getOpenTicketList())

    self.login()
    ticket = self.newRegularisationRequest(customer)
    self.tic()
    self.login(person.getUserId())
    self._test_ticket(ticket, initial_amount + 1)

    self.login()
    ticket = self.newRegularisationRequest(customer)
    self.tic()
    self.login(person.getUserId())
    self._test_ticket(ticket, initial_amount + 2)

  def test_upgrade_decision(self):
    project = self.addProject()
    person = self.makePerson(project, index=1, user=1)
    self.addProjectProductionManagerAssignment(person, project)
    person2 = self.makePerson(project, index=1, user=1)

    self.tic()

    self.portal.portal_skins.changeSkin('RSS')
    self.login(person.getUserId())

    initial_amount = len(
      self.portal.upgrade_decision_module.Folder_getOpenTicketList())

    self.login()
    ticket = self.newUpgradeDecision(person2, project, None)
    self.login(person.getUserId())
    self._test_upgrade_decision(ticket, initial_amount + 1)

    self.login()
    ticket = self.newUpgradeDecision(person2, project, None)
    self.login(person.getUserId())
    self._test_upgrade_decision(ticket, initial_amount + 2)

class TestSlapOSBase_getTicketRelatedEventList(TestRSSSyleSkinsMixin):

  def test_getTicketRelatedEventList_support_request_related_to_compute_node(self):
    self._test_getTicketRelatedEventList_support_request_related(
      self._makeComputeNode(self.addProject())[0])

  def test_getTicketRelatedEventList_support_request_related_to_instance_tree(self):
    self._test_getTicketRelatedEventList_support_request_related(
      self._makeInstanceTree())

  def _test_getTicketRelatedEventList_support_request_related(self, document):
    project = document.getFollowUpValue()
    ticket = self.newSupportRequest(self.makePerson(project), document)
    event = ticket.getFollowUpRelatedValue()

    person = self.makePerson(project, index=1, user=1)
    self.addProjectProductionManagerAssignment(person, project)
    self.tic()

    self.portal.portal_skins.changeSkin('RSS')
    self.login(person.getUserId())

    self.tic()
    open_related_ticket_list = document.Base_getTicketRelatedEventList()
    self.assertEqual(len(open_related_ticket_list), 1)
    self.assertNotEqual(open_related_ticket_list[0].pubDate, None)
    self.assertEqual(open_related_ticket_list[0].guid,
      '{}-{}'.format(event.getFollowUp(),
                     event.getRelativeUrl()))
    ticket.validate()
    self.tic()
    self.portal.portal_skins.changeSkin('RSS')
    open_related_ticket_list = document.Base_getTicketRelatedEventList()
    self.assertEqual(len(open_related_ticket_list), 1)
    self.assertNotEqual(open_related_ticket_list[0].pubDate, None)
    self.assertEqual(open_related_ticket_list[0].guid,
      '{}-{}'.format(event.getFollowUp(),
                     event.getRelativeUrl()))
    ticket.suspend()
    self.tic()
    self.portal.portal_skins.changeSkin('RSS')
    open_related_ticket_list = document.Base_getTicketRelatedEventList()
    self.assertEqual(len(open_related_ticket_list), 1)
    self.assertNotEqual(open_related_ticket_list[0].pubDate, None)
    self.assertEqual(open_related_ticket_list[0].guid,
      '{}-{}'.format(event.getFollowUp(),
                     event.getRelativeUrl()))

    ticket.invalidate()
    self.tic()
    self.portal.portal_skins.changeSkin('RSS')
    open_related_ticket_list = document.Base_getTicketRelatedEventList()
    self.assertEqual(len(open_related_ticket_list), 1)
    self.assertNotEqual(open_related_ticket_list[0].pubDate, None)
    self.assertNotEqual(open_related_ticket_list[0].link, None)
    self.assertIn(event.getTextContent(), open_related_ticket_list[0].description)
    self.assertEqual(open_related_ticket_list[0].guid,
      '{}-{}'.format(event.getFollowUp(),
                     event.getRelativeUrl()))
    self.assertEqual(open_related_ticket_list[0].title,
      ticket.getTitle())

  def test_getTicketRelatedEventList_cancelled_support_request_related_to_compute_node(self):
    self._test_getTicketRelatedEventList_cancelled_support_request_related(
      self._makeComputeNode(self.addProject())[0])

  def test_getTicketRelatedEventList_cancelled_support_request_related_to_instance_tree(self):
    self._test_getTicketRelatedEventList_cancelled_support_request_related(
      self._makeInstanceTree())

  def _test_getTicketRelatedEventList_cancelled_support_request_related(self, document):

    project = document.getFollowUpValue()
    ticket = self.newSupportRequest(self.makePerson(project), document)
    event = ticket.getFollowUpRelatedValue()

    person = self.makePerson(project, index=1, user=1)
    self.addProjectProductionManagerAssignment(person, project)
    self.tic()

    self.portal.portal_skins.changeSkin('RSS')
    self.login(person.getUserId())

    open_related_ticket_list = document.Base_getTicketRelatedEventList()
    self.assertEqual(len(open_related_ticket_list), 1)
    self.assertNotEqual(open_related_ticket_list[0].pubDate, None)
    self.assertNotEqual(open_related_ticket_list[0].link, None)
    self.assertIn(event.getTextContent(), open_related_ticket_list[0].description)
    self.assertEqual(open_related_ticket_list[0].guid,
      '{}-{}'.format(event.getFollowUp(),
                     event.getRelativeUrl()))
    self.assertEqual(open_related_ticket_list[0].title,
      ticket.getTitle())

    ticket.cancel()
    self.tic()
    self.portal.portal_skins.changeSkin('RSS')
    open_related_ticket_list = document.Base_getTicketRelatedEventList()
    self.assertEqual(len(open_related_ticket_list), 0)

  def test_getTicketRelatedEventList_upgrade_decision_related_to_compute_node(self):
    self._test_getTicketRelatedEventList_upgrade_decision_related(
      self._makeComputeNode(self.addProject())[0])

  def test_getTicketRelatedEventList_upgrade_decision_related_to_instance_tree(self):
    self._test_getTicketRelatedEventList_upgrade_decision_related(
      self._makeInstanceTree())

  def _test_getTicketRelatedEventList_upgrade_decision_related(self, document):
    project = document.getFollowUpValue()
    person = self.makePerson(project, index=1, user=1)
    self.addProjectProductionManagerAssignment(person, project)
    ticket = self.newUpgradeDecision(person, project, document)
    event = ticket.getFollowUpRelatedValue()
    self.tic()

    self.portal.portal_skins.changeSkin('RSS')
    self.login(person.getUserId())
    open_related_ticket_list = document.Base_getTicketRelatedEventList()
    # Not indexed yet
    self.assertEqual(len(open_related_ticket_list), 0)
    self.tic()

    self.portal.portal_skins.changeSkin('RSS')
    open_related_ticket_list = document.Base_getTicketRelatedEventList()
    self.assertEqual(len(open_related_ticket_list), 0)

    ticket.plan()
    self.tic()
    self.portal.portal_skins.changeSkin('RSS')
    open_related_ticket_list = document.Base_getTicketRelatedEventList()
    self.assertEqual(len(open_related_ticket_list), 0)

    ticket.confirm()
    self.tic()
    self.portal.portal_skins.changeSkin('RSS')
    open_related_ticket_list = document.Base_getTicketRelatedEventList()
    self.assertEqual(len(open_related_ticket_list), 1)
    self.assertNotEqual(open_related_ticket_list[0].pubDate, None)
    self.assertNotEqual(open_related_ticket_list[0].link, None)
    self.assertIn(event.getTextContent(), open_related_ticket_list[0].description)
    self.assertEqual(open_related_ticket_list[0].guid,
      '{}-{}'.format(event.getFollowUp(),
                     event.getRelativeUrl()))
    self.assertEqual(open_related_ticket_list[0].title,
      ticket.getTitle())

    ticket.start()
    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm',
                              "'disabled'", attribute='comment'):
      self.tic()
    self.portal.portal_skins.changeSkin('RSS')
    open_related_ticket_list = document.Base_getTicketRelatedEventList()
    self.assertEqual(len(open_related_ticket_list), 1)
    self.assertNotEqual(open_related_ticket_list[0].pubDate, None)
    self.assertNotEqual(open_related_ticket_list[0].link, None)
    self.assertIn(event.getTextContent(), open_related_ticket_list[0].description)
    self.assertEqual(open_related_ticket_list[0].guid,
      '{}-{}'.format(event.getFollowUp(),
                     event.getRelativeUrl()))
    self.assertEqual(open_related_ticket_list[0].title,
      ticket.getTitle())

    ticket.stop()
    self.tic()
    self.portal.portal_skins.changeSkin('RSS')
    open_related_ticket_list = document.Base_getTicketRelatedEventList()
    self.assertEqual(len(open_related_ticket_list), 1)
    self.assertNotEqual(open_related_ticket_list[0].pubDate, None)
    self.assertNotEqual(open_related_ticket_list[0].link, None)
    self.assertIn(event.getTextContent(), open_related_ticket_list[0].description)
    self.assertEqual(open_related_ticket_list[0].guid,
      '{}-{}'.format(event.getFollowUp(),
                     event.getRelativeUrl()))
    self.assertEqual(open_related_ticket_list[0].title,
      ticket.getTitle())


    ticket.deliver()
    self.tic()
    self.portal.portal_skins.changeSkin('RSS')
    open_related_ticket_list = document.Base_getTicketRelatedEventList()
    self.assertEqual(len(open_related_ticket_list), 1)
    self.assertNotEqual(open_related_ticket_list[0].pubDate, None)
    self.assertNotEqual(open_related_ticket_list[0].link, None)
    self.assertIn(event.getTextContent(), open_related_ticket_list[0].description)
    self.assertEqual(open_related_ticket_list[0].guid,
      '{}-{}'.format(event.getFollowUp(),
                     event.getRelativeUrl()))
    self.assertEqual(open_related_ticket_list[0].title,
      ticket.getTitle())

  def test_getTicketRelatedEventList_cancelled_upgrade_decision_related_to_instance_tree(self):
    self._test_getTicketRelatedEventList_cancelled_upgrade_decision_related(
      self._makeInstanceTree())

  def _test_getTicketRelatedEventList_cancelled_upgrade_decision_related(self, document):
    project = document.getFollowUpValue()
    person = self.makePerson(project, index=1, user=1)
    self.addProjectProductionManagerAssignment(person, project)
    ticket = self.newUpgradeDecision(person, project, document)
    self.tic()

    self.portal.portal_skins.changeSkin('RSS')
    self.login(person.getUserId())
    open_related_ticket_list = document.Base_getTicketRelatedEventList()
    # Not indexed yet
    self.assertEqual(len(open_related_ticket_list), 0)

    self.tic()

    self.portal.portal_skins.changeSkin('RSS')
    open_related_ticket_list = document.Base_getTicketRelatedEventList()
    self.assertEqual(len(open_related_ticket_list), 0)

    ticket.cancel()
    self.tic()
    self.portal.portal_skins.changeSkin('RSS')
    open_related_ticket_list = document.Base_getTicketRelatedEventList()
    self.assertEqual(len(open_related_ticket_list), 0)

class TestSlapOSBase_getEventList(TestRSSSyleSkinsMixin):

  def test_Base_getEventList(self):
    # Base_getEventList is already widely tested on Base_getTicketRelatedEventList
    # and Folder_getOpenTicketList, so we only tested the specific use case of 
    # all events togheter
    instance_tree = self._makeInstanceTree()
    project = instance_tree.getFollowUpValue()
    person = self.makePerson(project, index=1, user=1)
    self.tic()

    self.portal.portal_skins.changeSkin('RSS')
    self.login(person.getUserId())

    self.login()
    ticket = self.newSupportRequest(person, instance_tree)
    self.login(person.getUserId())

    event = ticket.getFollowUpRelatedValue()
    self.assertNotEqual(event, None)

    self.portal.portal_skins.changeSkin('RSS')
    open_ticket_list = self.portal.Base_getEventList()
    self.assertEqual(len(open_ticket_list), 1)
    self.assertNotEqual(open_ticket_list[0].pubDate, None)
    self.assertEqual(open_ticket_list[0].guid,
      '{}-{}'.format(event.getFollowUp(),
                     event.getRelativeUrl()))

    self.login()
    ticket.validate()
    self.tic()
    self.login(person.getUserId())

    self.portal.portal_skins.changeSkin('RSS')
    open_ticket_list = self.portal.Base_getEventList()
    self.assertEqual(len(open_ticket_list), 1)
    self.assertNotEqual(open_ticket_list[0].pubDate, None)
    self.assertEqual(open_ticket_list[0].guid,
      '{}-{}'.format(event.getFollowUp(),
                     event.getRelativeUrl()))

    self.login()
    ticket.suspend()
    self.tic()
    self.login(person.getUserId())

    self.portal.portal_skins.changeSkin('RSS')
    open_ticket_list = self.portal.Base_getEventList()
    self.assertEqual(len(open_ticket_list), 1)
    self.assertNotEqual(open_ticket_list[0].pubDate, None)
    self.assertEqual(open_ticket_list[0].guid,
      '{}-{}'.format(event.getFollowUp(),
                     event.getRelativeUrl()))

    self.login()
    ticket.invalidate()
    self.tic()
    self.login(person.getUserId())

    self.portal.portal_skins.changeSkin('RSS')
    open_ticket_list = self.portal.Base_getEventList()
    self.assertEqual(len(open_ticket_list), 1)
    # Extra checks
    self.assertNotEqual(open_ticket_list[0].pubDate, None)
    self.assertNotEqual(open_ticket_list[0].link, None)
    self.assertIn(event.getTextContent(), open_ticket_list[0].description)
    self.assertEqual(open_ticket_list[0].guid,
      '{}-{}'.format(event.getFollowUp(),
                     event.getRelativeUrl()))
    self.assertEqual(open_ticket_list[0].title,
      ticket.getTitle())

    # Now include a Regulatisation Request
    sleep(2)
    self.login()
    regularisation_request = self.newRegularisationRequest(person)
    self.login(person.getUserId())

    event_rr = regularisation_request.getFollowUpRelatedValue()
    self.assertNotEqual(event_rr, None)

    self.portal.portal_skins.changeSkin('RSS')
    open_ticket_list = self.portal.Base_getEventList()
    self.assertEqual(len(open_ticket_list), 2)
    self.assertNotEqual(open_ticket_list[0].pubDate, None)
    self.assertEqual(open_ticket_list[0].guid,
      '{}-{}'.format(event_rr.getFollowUp(),
                     event_rr.getRelativeUrl()))

    # check if previous still the same
    self.assertEqual(open_ticket_list[1].guid,
      '{}-{}'.format(event.getFollowUp(),
                     event.getRelativeUrl()))

    self.login()
    regularisation_request.validate()
    self.tic()
    self.login(person.getUserId())

    self.portal.portal_skins.changeSkin('RSS')
    open_ticket_list = self.portal.Base_getEventList()
    self.assertEqual(len(open_ticket_list), 2)
    self.assertNotEqual(open_ticket_list[0].pubDate, None)
    self.assertEqual(open_ticket_list[0].guid,
      '{}-{}'.format(event_rr.getFollowUp(),
                     event_rr.getRelativeUrl()))

    self.login()
    regularisation_request.suspend()
    self.tic()
    self.login(person.getUserId())

    self.portal.portal_skins.changeSkin('RSS')
    open_ticket_list = self.portal.Base_getEventList()
    self.assertEqual(len(open_ticket_list), 2)
    self.assertNotEqual(open_ticket_list[0].pubDate, None)
    self.assertEqual(open_ticket_list[0].guid,
      '{}-{}'.format(event_rr.getFollowUp(),
                     event_rr.getRelativeUrl()))

    self.login()
    regularisation_request.invalidate()
    self.tic()
    self.login(person.getUserId())

    self.portal.portal_skins.changeSkin('RSS')
    open_ticket_list = self.portal.Base_getEventList()
    self.assertEqual(len(open_ticket_list), 2)
    # Extra checks
    self.assertNotEqual(open_ticket_list[0].pubDate, None)
    self.assertNotEqual(open_ticket_list[0].link, None)
    self.assertIn(event_rr.getTextContent(), open_ticket_list[0].description)
    self.assertEqual(open_ticket_list[0].guid,
      '{}-{}'.format(event_rr.getFollowUp(),
                     event_rr.getRelativeUrl()))
    self.assertEqual(open_ticket_list[0].title,
      regularisation_request.getTitle())

    # Now add one Upgrade Decision

    self.login()
    sleep(2)
    upgrade_decision = self.newUpgradeDecision(person, None, None)
    self.login(person.getUserId())

    event_ud = upgrade_decision.getFollowUpRelatedValue()
    self.assertNotEqual(event_ud, None)
    self.portal.portal_skins.changeSkin('RSS')
    open_ticket_list = self.portal.Base_getEventList()
    self.assertEqual(len(open_ticket_list), 2)

    self.login()
    upgrade_decision.plan()
    self.tic()
    self.login(person.getUserId())

    self.portal.portal_skins.changeSkin('RSS')
    open_ticket_list = self.portal.Base_getEventList()
    self.assertEqual(len(open_ticket_list), 2)

    self.login()
    upgrade_decision.confirm()
    self.tic()
    self.login(person.getUserId())

    self.portal.portal_skins.changeSkin('RSS')
    open_ticket_list = self.portal.Base_getEventList()
    self.assertEqual(len(open_ticket_list), 3)
    self.assertNotEqual(open_ticket_list[0].pubDate, None)
    self.assertEqual(open_ticket_list[0].guid,
      '{}-{}'.format(event_ud.getFollowUp(),
                     event_ud.getRelativeUrl()))

    self.login()
    upgrade_decision.start()
    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm',
                              "'disabled'", attribute='comment'):
      self.tic()
    self.login(person.getUserId())

    self.portal.portal_skins.changeSkin('RSS')
    open_ticket_list = self.portal.Base_getEventList()
    self.assertEqual(len(open_ticket_list), 3)
    self.assertNotEqual(open_ticket_list[0].pubDate, None)
    self.assertEqual(open_ticket_list[0].guid,
      '{}-{}'.format(event_ud.getFollowUp(),
                     event_ud.getRelativeUrl()))

    self.login()
    upgrade_decision.stop()
    self.tic()
    self.login(person.getUserId())

    self.portal.portal_skins.changeSkin('RSS')
    open_ticket_list = self.portal.Base_getEventList()
    self.assertEqual(len(open_ticket_list), 3)
    self.assertNotEqual(open_ticket_list[0].pubDate, None)
    self.assertEqual(open_ticket_list[0].guid,
      '{}-{}'.format(event_ud.getFollowUp(),
                     event_ud.getRelativeUrl()))

    self.login()
    upgrade_decision.deliver()
    self.tic()
    self.login(person.getUserId())

    self.portal.portal_skins.changeSkin('RSS')
    open_ticket_list = self.portal.Base_getEventList()
    self.assertEqual(len(open_ticket_list), 3)
    self.assertNotEqual(open_ticket_list[0].pubDate, None)
    self.assertEqual(open_ticket_list[0].guid,
      '{}-{}'.format(event_ud.getFollowUp(),
                     event_ud.getRelativeUrl()))

    # check if ordering is correct.
    self.assertEqual(open_ticket_list[0].title,
      upgrade_decision.getTitle())

    self.assertEqual(open_ticket_list[1].title,
      regularisation_request.getTitle())

    self.assertEqual(open_ticket_list[2].title,
      ticket.getTitle())

class TestBase_getTicketUrl(TestRSSSyleSkinsMixin):
  def test_Base_getTicketUrl(self):
    ticket = self.portal.support_request_module.newContent(\
                      title="Test Support Request %s" % self.new_id)

    self.portal.portal_skins.changeSkin('RSS')
    self.assertIn("/#/%s" % ticket.getRelativeUrl(),
                  ticket.Base_getTicketUrl())

    self.assertIn("%s/#/" % self.portal.absolute_url(),
                  ticket.Base_getTicketUrl())

    web_site = self.portal.web_site_module.slapos_master_panel
    self.assertIn("%s/#/" % web_site.absolute_url(),
                  web_site.support_request_module[ticket.getId()].Base_getTicketUrl())

    self.assertIn("/#/%s" % ticket.getRelativeUrl(),
                  web_site.support_request_module[ticket.getId()].Base_getTicketUrl())


class TestSlapOSSaleInvoiceTransaction_getRSSTitleAndDescription(TestRSSSyleSkinsMixin):

  def test_sale_invoice(self):
    invoice = self.portal.accounting_module.newContent(\
                      portal_type="Sale Invoice Transaction",
                      reference="TESTINVOICE-%s" % self.new_id,
                      title="Test Sale Invoice %s" % self.new_id)

    self.portal.portal_skins.changeSkin('RSS')
    text = self.portal.Base_translateString("Invoice")
    self.assertEqual(
      invoice.SaleInvoiceTransaction_getRSSTitle(),
      "%s %s" % (text, invoice.getReference()))

    self.assertIn(
      invoice.Base_getTicketUrl(),
      invoice.SaleInvoiceTransaction_getRSSDescription())

    self.assertIn(
      invoice.getReference(),
      invoice.SaleInvoiceTransaction_getRSSDescription())

    invoice_via_website = \
      self.portal.web_site_module.slapos_master_panel.accounting_module[invoice.getId()]
    self.assertEqual(
      invoice_via_website.SaleInvoiceTransaction_getRSSTitle(),
      "[SlapOS Master Panel] %s %s" % (text, invoice.getReference()))

    self.assertNotIn(
      invoice.Base_getTicketUrl(),
      invoice_via_website.SaleInvoiceTransaction_getRSSDescription())

    self.assertIn(
      invoice_via_website.Base_getTicketUrl(),
      invoice_via_website.SaleInvoiceTransaction_getRSSDescription())

    invoice.setStartDate(DateTime("02/01/2018"))
    self.assertEqual(
      invoice_via_website.SaleInvoiceTransaction_getRSSTitle(),
      "[SlapOS Master Panel] %s %s - (01/02/2018)" % (text, invoice.getReference()))

  
