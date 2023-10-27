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
from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixinWithAbort
from DateTime import DateTime
import feedparser

def getFakeSlapState():
  return "destroy_requested"

class TestRSSSyleSkinsMixin(SlapOSTestCaseMixinWithAbort):

  def afterSetUp(self):
    SlapOSTestCaseMixinWithAbort.afterSetUp(self)
    self.person = self.makePerson(new_id=self.new_id, index=0, user=0)
    self.clearCache()

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
       .software_installation_module.newContent(portal_type="Software Installation")
    software_installation.edit(
       url_string=self.generateNewSoftwareReleaseUrl(),
       aggregate=self.compute_node.getRelativeUrl(),
       reference='TESTSOFTINSTS-%s' % self.generateNewId(),
       title='Start requested for %s' % self.compute_node.getUid()
     )
    software_installation.validate()
    software_installation.requestStart()

    return software_installation


class TestSlapOSEvent_getRSSTextContent(TestRSSSyleSkinsMixin):

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

    self.portal.portal_skins.changeSkin('RSS')
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

class TestSlapOSSupportRequestRSS(TestRSSSyleSkinsMixin):

  def test_WebSection_viewTicketListAsRSS(self):
    person = self.makePerson()

    module = self.portal.support_request_module
    support_request = module.newContent(
        portal_type="Support Request",
        title='Help',
        destination_decision_value=person,
    )
    self.portal.event_module.newContent(
        portal_type='Web Message',
        follow_up_value=support_request,
        text_content='I need help !',
        start_date = DateTime(),
        source_value=person,
        destination_value=self.portal.organisation_module.slapos,
        resource_value=self.portal.service_module.slapos_crm_monitoring
    ).start()
    support_request.validate()
    self.clearCache()
    self.tic()

    self.login(person.getUserId())
    self.portal.portal_skins.changeSkin('RSS')
    self.clearCache()
    transaction.commit()
    parsed = feedparser.parse(self.portal.WebSection_viewTicketListAsRSS())
    self.assertFalse(parsed.bozo)
    first_entry_id = [item.id for item in parsed.entries]
    self.assertEqual([item.summary for item in parsed.entries], ['I need help !'])

    self.portal.event_module.newContent(
        portal_type='Web Message',
        follow_up_value=support_request,
        text_content='How can I help you ?',
        start_date = DateTime(),
        destination_value=person,
        source_value=self.portal.organisation_module.slapos,
        resource_value=self.portal.service_module.slapos_crm_monitoring
    ).start()
    self.clearCache()
    self.tic()

    self.portal.portal_skins.changeSkin('RSS')
    self.clearCache()
    transaction.commit()
    parsed = feedparser.parse(self.portal.WebSection_viewTicketListAsRSS())
    self.assertFalse(parsed.bozo)
    self.assertEqual([item.summary for item in parsed.entries],
      ['How can I help you ?', 'I need help !'])
    self.assertNotEqual([item.id for item in parsed.entries][0], first_entry_id)

  def test_WebSection_viewCriticalTicketListAsRSS(self):
    person = self.makePerson()

    module = self.portal.support_request_module
    support_request = module.newContent(
        portal_type="Support Request",
        title='Help',
        destination_decision_value=person,
    )
    self.portal.event_module.newContent(
        portal_type='Web Message',
        follow_up_value=support_request,
        text_content='I need help !',
        source_value=person,
        start_date = DateTime(),
        destination_value=self.portal.organisation_module.slapos,
        resource_value=self.portal.service_module.slapos_crm_monitoring
    ).start()
    support_request.validate()
    self.clearCache()
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

    self.portal.event_module.newContent(
        portal_type='Web Message',
        follow_up_value=support_request,
        text_content='How can I help you ?',
        start_date = DateTime(),
        destination_value=person,
        source_value=self.portal.organisation_module.slapos,
        resource_value=self.portal.service_module.slapos_crm_monitoring
    ).start()
    self.clearCache()
    self.tic()

    self.portal.portal_skins.changeSkin('RSS')
    self.clearCache()
    transaction.commit()
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
    open_ticket_list = module.Folder_getOpenTicketList()
    self.assertEqual(len(open_ticket_list), expected_amount-1)

    ticket.submit()
    ticket.immediateReindexObject()
    open_ticket_list = module.Folder_getOpenTicketList()
    self.assertEqual(len(open_ticket_list), expected_amount)
    self.assertNotEqual(open_ticket_list[0].pubDate, None)
    self.assertEqual(open_ticket_list[0].guid,
      '{}-{}'.format(event.getFollowUp(),
                     event.getRelativeUrl()))

    ticket.validate()
    ticket.immediateReindexObject()
    open_ticket_list = module.Folder_getOpenTicketList()
    self.assertEqual(len(open_ticket_list), expected_amount)
    self.assertNotEqual(open_ticket_list[0].pubDate, None)
    self.assertEqual(open_ticket_list[0].guid,
      '{}-{}'.format(event.getFollowUp(),
                     event.getRelativeUrl()))
    ticket.suspend()
    ticket.immediateReindexObject()
    open_ticket_list = module.Folder_getOpenTicketList()
    self.assertEqual(len(open_ticket_list), expected_amount)
    self.assertNotEqual(open_ticket_list[0].pubDate, None)
    self.assertEqual(open_ticket_list[0].guid,
      '{}-{}'.format(event.getFollowUp(),
                     event.getRelativeUrl()))
    ticket.invalidate()
    ticket.immediateReindexObject()
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
    open_ticket_list = module.Folder_getOpenTicketList()
    self.assertEqual(len(open_ticket_list), expected_amount-1)

    ticket.plan()
    ticket.immediateReindexObject()
    open_ticket_list = module.Folder_getOpenTicketList()
    self.assertEqual(len(open_ticket_list), expected_amount-1)

    ticket.confirm()
    ticket.immediateReindexObject()
    open_ticket_list = module.Folder_getOpenTicketList()
    self.assertEqual(len(open_ticket_list), expected_amount)

    self.assertNotEqual(open_ticket_list[0].pubDate, None)
    self.assertEqual(open_ticket_list[0].guid,
      '{}-{}'.format(event.getFollowUp(),
                     event.getRelativeUrl()))

    ticket.start()
    ticket.immediateReindexObject()
    open_ticket_list = module.Folder_getOpenTicketList()
    self.assertEqual(len(open_ticket_list), expected_amount)
    self.assertNotEqual(open_ticket_list[0].pubDate, None)
    self.assertEqual(open_ticket_list[0].guid,
      '{}-{}'.format(event.getFollowUp(),
                     event.getRelativeUrl()))

    ticket.stop()
    ticket.immediateReindexObject()
    open_ticket_list = module.Folder_getOpenTicketList()
    self.assertEqual(len(open_ticket_list), expected_amount)
    self.assertNotEqual(open_ticket_list[0].pubDate, None)
    self.assertEqual(open_ticket_list[0].guid,
      '{}-{}'.format(event.getFollowUp(),
                     event.getRelativeUrl()))

    ticket.deliver()
    ticket.immediateReindexObject()
    open_ticket_list = module.Folder_getOpenTicketList()
    self.assertEqual(len(open_ticket_list), expected_amount)
    self.assertNotEqual(open_ticket_list[0].pubDate, None)
    self.assertEqual(open_ticket_list[0].guid,
      '{}-{}'.format(event.getFollowUp(),
                     event.getRelativeUrl()))

  def test_support_request(self):
    def newSupportRequest():
      self.portal.portal_skins.changeSkin('View')
      person = self.makePerson()
      sr = self.portal.support_request_module.newContent(\
                        title="Test Support Request %s" % self.new_id)
      event = self.portal.event_module.newContent(
        portal_type='Web Message',
        follow_up_value=sr,
        text_content="Test Support Request %s" % self.new_id,
        start_date = DateTime(),
        source_value=person,
        destination_value=self.portal.organisation_module.slapos,
        resource_value=self.portal.service_module.slapos_crm_monitoring
      )
      event.start()
      event.immediateReindexObject()
      sr.immediateReindexObject()
      self.portal.portal_skins.changeSkin('RSS')
      return sr

    person = self.makePerson(index=1, user=1)
    person.newContent(portal_type="Assignment",
                      group="company").open()
    self.tic()

    self.portal.portal_skins.changeSkin('RSS')
    self.login(person.getUserId())

    initial_amount = len(
      self.portal.support_request_module.Folder_getOpenTicketList())

    self.login()
    ticket = newSupportRequest()
    self.login(person.getUserId())
    self._test_ticket(ticket, initial_amount + 1)

    self.login()
    ticket = newSupportRequest()
    self.login(person.getUserId())
    self._test_ticket(ticket, initial_amount + 2)

  def test_regularisation_request(self):
    def newRegularisationRequest():
      self.portal.portal_skins.changeSkin('View')
      person = self.makePerson()
      ticket = self.portal.regularisation_request_module.newContent(
        portal_type='Regularisation Request',
        title="Test Reg. Req.%s" % self.new_id,
        reference="TESTREGREQ-%s" % self.new_id
        )

      event = self.portal.event_module.newContent(
        portal_type='Web Message',
        follow_up_value=ticket,
        text_content=ticket.getTitle(),
        start_date = DateTime(),
        source_value=person,
        destination_value=self.portal.organisation_module.slapos,
        resource_value=self.portal.service_module.slapos_crm_monitoring
      )
      ticket.immediateReindexObject()
      event.start()
      event.immediateReindexObject()
      self.portal.portal_skins.changeSkin('RSS')
      return ticket

    person = self.makePerson(index=1, user=1)
    person.newContent(portal_type="Assignment",
                      group="company").open()
    self.tic()

    self.portal.portal_skins.changeSkin('RSS')
    self.login(person.getUserId())

    initial_amount = len(
      self.portal.regularisation_request_module.Folder_getOpenTicketList())

    self.login()
    ticket = newRegularisationRequest()
    self.login(person.getUserId())
    self._test_ticket(ticket, initial_amount + 1)

    self.login()
    ticket = newRegularisationRequest()
    self.login(person.getUserId())
    self._test_ticket(ticket, initial_amount + 2)

  def test_upgrade_decision(self):
    def newUpgradeDecision():
      self.portal.portal_skins.changeSkin('View')
      person = self.makePerson()
      ticket = self.portal.upgrade_decision_module.newContent(
        portal_type='Upgrade Decision',
        title="Upgrade Decision Test %s" % self.new_id,
        reference="TESTUD-%s" % self.new_id)

      event = self.portal.event_module.newContent(
        portal_type='Web Message',
        follow_up_value=ticket,
        text_content=ticket.getTitle(),
        start_date = DateTime(),
        source_value=person,
        destination_value=self.portal.organisation_module.slapos,
        resource_value=self.portal.service_module.slapos_crm_monitoring
      )
      ticket.immediateReindexObject()
      event.start()
      event.immediateReindexObject()
      self.portal.portal_skins.changeSkin('RSS')
      return ticket


    person = self.makePerson(index=1, user=1)
    person.newContent(portal_type="Assignment",
                      group="company").open()
    self.tic()

    self.portal.portal_skins.changeSkin('RSS')
    self.login(person.getUserId())

    initial_amount = len(
      self.portal.upgrade_decision_module.Folder_getOpenTicketList())

    self.login()
    ticket = newUpgradeDecision()
    self.login(person.getUserId())
    self._test_upgrade_decision(ticket, initial_amount + 1)

    self.login()
    ticket = newUpgradeDecision()
    self.login(person.getUserId())
    self._test_upgrade_decision(ticket, initial_amount + 2)

class TestSlapOSBase_getTicketRelatedEventList(TestRSSSyleSkinsMixin):

  def newSupportRequest(self):
    self.portal.portal_skins.changeSkin('View')
    person = self.makePerson()
    sr = self.portal.support_request_module.newContent(\
                      title="Test Support Request %s" % self.new_id)
    event = self.portal.event_module.newContent(
      portal_type='Web Message',
      follow_up_value=sr,
      text_content="Test Support Request %s" % self.new_id,
      start_date = DateTime(),
      source_value=person,
      destination_value=self.portal.organisation_module.slapos,
      resource_value=self.portal.service_module.slapos_crm_monitoring
    )
    event.start()
    event.immediateReindexObject()
    sr.immediateReindexObject()
    return sr

  def test_getTicketRelatedEventList_support_request_related_to_compute_node(self):
    self._test_getTicketRelatedEventList_support_request_related(
      self._makeComputeNode()[0])

  def test_getTicketRelatedEventList_support_request_related_to_instance_tree(self):
    self._test_getTicketRelatedEventList_support_request_related(
      self._makeInstanceTree())

  def _test_getTicketRelatedEventList_support_request_related(self, document):
    ticket = self.newSupportRequest()
    ticket.setAggregateValue(document)
    event = ticket.getFollowUpRelatedValue()

    person = self.makePerson(index=1, user=1)
    person.newContent(portal_type="Assignment",
                      group="company").open()
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

    ticket.submit()
    ticket.immediateReindexObject()
    open_related_ticket_list = document.Base_getTicketRelatedEventList()
    self.assertEqual(len(open_related_ticket_list), 1)
    self.assertNotEqual(open_related_ticket_list[0].pubDate, None)
    self.assertEqual(open_related_ticket_list[0].guid,
      '{}-{}'.format(event.getFollowUp(),
                     event.getRelativeUrl()))
    ticket.validate()
    ticket.immediateReindexObject()
    open_related_ticket_list = document.Base_getTicketRelatedEventList()
    self.assertEqual(len(open_related_ticket_list), 1)
    self.assertNotEqual(open_related_ticket_list[0].pubDate, None)
    self.assertEqual(open_related_ticket_list[0].guid,
      '{}-{}'.format(event.getFollowUp(),
                     event.getRelativeUrl()))
    ticket.suspend()
    ticket.immediateReindexObject()
    open_related_ticket_list = document.Base_getTicketRelatedEventList()
    self.assertEqual(len(open_related_ticket_list), 1)
    self.assertNotEqual(open_related_ticket_list[0].pubDate, None)
    self.assertEqual(open_related_ticket_list[0].guid,
      '{}-{}'.format(event.getFollowUp(),
                     event.getRelativeUrl()))

    ticket.invalidate()
    ticket.immediateReindexObject()
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
      self._makeComputeNode()[0])

  def test_getTicketRelatedEventList_cancelled_support_request_related_to_instance_tree(self):
    self._test_getTicketRelatedEventList_cancelled_support_request_related(
      self._makeInstanceTree())

  def _test_getTicketRelatedEventList_cancelled_support_request_related(self, document):

    ticket = self.newSupportRequest()
    ticket.setAggregateValue(document)
    event = ticket.getFollowUpRelatedValue()
    person = self.makePerson(index=1, user=1)
    person.newContent(portal_type="Assignment",
                      group="company").open()
    self.tic()

    self.portal.portal_skins.changeSkin('RSS')
    self.login(person.getUserId())
    open_related_ticket_list = document.Base_getTicketRelatedEventList()
    # Not indexed yet
    self.assertEqual(len(open_related_ticket_list), 0)
    self.tic()

    open_related_ticket_list = document.Base_getTicketRelatedEventList()
    self.assertEqual(len(open_related_ticket_list), 0)

    ticket.submit()
    ticket.immediateReindexObject()
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
    ticket.immediateReindexObject()
    open_related_ticket_list = document.Base_getTicketRelatedEventList()
    self.assertEqual(len(open_related_ticket_list), 0)

  def makeUpgradeDecision(self):
    self.portal.portal_skins.changeSkin('View')
    person = self.makePerson()
    ticket = self.portal.upgrade_decision_module.newContent(
      portal_type='Upgrade Decision',
      title="Upgrade Decision Test %s" % self.new_id,
      reference="TESTUD-%s" % self.new_id)
    event = self.portal.event_module.newContent(
      portal_type='Web Message',
      follow_up_value=ticket,
      text_content=ticket.getTitle(),
      start_date = DateTime(),
      source_value=person,
      destination_value=self.portal.organisation_module.slapos,
      resource_value=self.portal.service_module.slapos_crm_monitoring
    )
    ticket.immediateReindexObject()
    event.start()
    event.immediateReindexObject()
    return ticket

  def test_getTicketRelatedEventList_upgrade_decision_related_to_compute_node(self):
    self._test_getTicketRelatedEventList_upgrade_decision_related(
      self._makeComputeNode()[0])

  def test_getTicketRelatedEventList_upgrade_decision_related_to_instance_tree(self):
    self._test_getTicketRelatedEventList_upgrade_decision_related(
      self._makeInstanceTree())

  def _test_getTicketRelatedEventList_upgrade_decision_related(self, document):
    ticket = self.makeUpgradeDecision()
    person = self.makePerson(index=1, user=1)
    ticket.newContent(
      portal_type="Upgrade Decision Line"
    ).setAggregateValue(document)
    person.newContent(portal_type="Assignment",
                      group="company").open()
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
    ticket.immediateReindexObject()
    open_related_ticket_list = document.Base_getTicketRelatedEventList()
    self.assertEqual(len(open_related_ticket_list), 0)

    ticket.confirm()
    ticket.immediateReindexObject()
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
    ticket.immediateReindexObject()
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
    ticket.immediateReindexObject()
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
    ticket.immediateReindexObject()
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


  def test_getTicketRelatedEventList_cancelled_upgrade_decision_related_to_compute_node(self):
    self._test_getTicketRelatedEventList_cancelled_upgrade_decision_related(
      self._makeComputeNode()[0])

  def test_getTicketRelatedEventList_cancelled_upgrade_decision_related_to_instance_tree(self):
    self._test_getTicketRelatedEventList_cancelled_upgrade_decision_related(
      self._makeInstanceTree())

  def _test_getTicketRelatedEventList_cancelled_upgrade_decision_related(self, document):
    ticket = self.makeUpgradeDecision()
    person = self.makePerson(index=1, user=1)
    ticket.newContent(
      portal_type="Upgrade Decision Line"
    ).setAggregateValue(document)
    person.newContent(portal_type="Assignment",
                      group="company").open()
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
    ticket.immediateReindexObject()
    open_related_ticket_list = document.Base_getTicketRelatedEventList()
    self.assertEqual(len(open_related_ticket_list), 0)

class TestSlapOSBase_getEventList(TestRSSSyleSkinsMixin):

  def testBase_getEventList(self):
    # Base_getEventList is already widely tested on Base_getTicketRelatedEventList
    # and Folder_getOpenTicketList, so we only tested the specific use case of 
    # all events togheter
    def newSupportRequest(person):
      self.portal.portal_skins.changeSkin('View')
      sr = self.portal.support_request_module.newContent(\
                        destination_decision_value=person,
                        title="Test Support Request %s" % self.new_id)
      event = self.portal.event_module.newContent(
        portal_type='Web Message',
        follow_up_value=sr,
        text_content="Test Support Request %s" % self.new_id,
        start_date = DateTime()-0.01,
        source_value=person,
        destination_value=self.portal.organisation_module.slapos,
        resource_value=self.portal.service_module.slapos_crm_monitoring
      )
      sr.updateLocalRolesOnSecurityGroups()
      event.start()
      event.immediateReindexObject()
      sr.immediateReindexObject()
      self.portal.portal_skins.changeSkin('RSS')
      return sr

    person = self.makePerson(index=1, user=1)
    self.tic()

    self.portal.portal_skins.changeSkin('RSS')
    self.login(person.getUserId())

    self.login()
    ticket = newSupportRequest(person)
    self.login(person.getUserId())

    event = ticket.getFollowUpRelatedValue()
    self.assertNotEqual(event, None)
    open_ticket_list = self.portal.Base_getEventList()
    self.assertEqual(len(open_ticket_list), 0)

    self.login()
    ticket.submit()
    ticket.immediateReindexObject()
    self.login(person.getUserId())

    open_ticket_list = self.portal.Base_getEventList()
    self.assertEqual(len(open_ticket_list), 1)
    self.assertNotEqual(open_ticket_list[0].pubDate, None)
    self.assertEqual(open_ticket_list[0].guid,
      '{}-{}'.format(event.getFollowUp(),
                     event.getRelativeUrl()))

    self.login()
    ticket.validate()
    ticket.immediateReindexObject()
    self.login(person.getUserId())

    open_ticket_list = self.portal.Base_getEventList()
    self.assertEqual(len(open_ticket_list), 1)
    self.assertNotEqual(open_ticket_list[0].pubDate, None)
    self.assertEqual(open_ticket_list[0].guid,
      '{}-{}'.format(event.getFollowUp(),
                     event.getRelativeUrl()))

    self.login()
    ticket.suspend()
    ticket.immediateReindexObject()
    self.login(person.getUserId())

    open_ticket_list = self.portal.Base_getEventList()
    self.assertEqual(len(open_ticket_list), 1)
    self.assertNotEqual(open_ticket_list[0].pubDate, None)
    self.assertEqual(open_ticket_list[0].guid,
      '{}-{}'.format(event.getFollowUp(),
                     event.getRelativeUrl()))

    self.login()
    ticket.invalidate()
    ticket.immediateReindexObject()
    self.login(person.getUserId())

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
    def newRegularisationRequest(person):
      self.portal.portal_skins.changeSkin('View')
      ticket = self.portal.regularisation_request_module.newContent(
        portal_type='Regularisation Request',
        title="Test Reg. Req.%s" % self.new_id,
        reference="TESTREGREQ-%s" % self.new_id,
        destination_decision_value=person)

      event = self.portal.event_module.newContent(
        portal_type='Web Message',
        follow_up_value=ticket,
        text_content=ticket.getTitle(),
        start_date = DateTime()-0.005,
        source_value=person,
        destination_value=self.portal.organisation_module.slapos,
        resource_value=self.portal.service_module.slapos_crm_monitoring
      )
      ticket.immediateReindexObject()
      ticket.updateLocalRolesOnSecurityGroups()
      event.start()
      event.immediateReindexObject()
      self.portal.portal_skins.changeSkin('RSS')
      return ticket

    self.login()
    regularisation_request = newRegularisationRequest(person)
    self.login(person.getUserId())

    event_rr = regularisation_request.getFollowUpRelatedValue()
    self.assertNotEqual(event_rr, None)
    open_ticket_list = self.portal.Base_getEventList()
    self.assertEqual(len(open_ticket_list), 1)

    self.login()
    regularisation_request.submit()
    regularisation_request.immediateReindexObject()
    self.login(person.getUserId())

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
    regularisation_request.immediateReindexObject()
    self.login(person.getUserId())

    open_ticket_list = self.portal.Base_getEventList()
    self.assertEqual(len(open_ticket_list), 2)
    self.assertNotEqual(open_ticket_list[0].pubDate, None)
    self.assertEqual(open_ticket_list[0].guid,
      '{}-{}'.format(event_rr.getFollowUp(),
                     event_rr.getRelativeUrl()))

    self.login()
    regularisation_request.suspend()
    regularisation_request.immediateReindexObject()
    self.login(person.getUserId())

    open_ticket_list = self.portal.Base_getEventList()
    self.assertEqual(len(open_ticket_list), 2)
    self.assertNotEqual(open_ticket_list[0].pubDate, None)
    self.assertEqual(open_ticket_list[0].guid,
      '{}-{}'.format(event_rr.getFollowUp(),
                     event_rr.getRelativeUrl()))

    self.login()
    regularisation_request.invalidate()
    regularisation_request.immediateReindexObject()
    self.login(person.getUserId())

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
    def newUpgradeDecision(person):
      self.portal.portal_skins.changeSkin('View')
      ticket = self.portal.upgrade_decision_module.newContent(
        portal_type='Upgrade Decision',
        title="Upgrade Decision Test %s" % self.new_id,
        reference="TESTUD-%s" % self.new_id,
        destination_decision_value=person)

      event = self.portal.event_module.newContent(
        portal_type='Web Message',
        follow_up_value=ticket,
        text_content=ticket.getTitle(),
        start_date = DateTime(),
        source_value=person,
        destination_value=self.portal.organisation_module.slapos,
        resource_value=self.portal.service_module.slapos_crm_monitoring
      )
      ticket.updateLocalRolesOnSecurityGroups()
      ticket.immediateReindexObject()
      event.start()
      event.immediateReindexObject()
      self.portal.portal_skins.changeSkin('RSS')
      return ticket

    self.login()
    upgrade_decision = newUpgradeDecision(person)
    self.login(person.getUserId())

    event_ud = upgrade_decision.getFollowUpRelatedValue()
    self.assertNotEqual(event_ud, None)
    open_ticket_list = self.portal.Base_getEventList()
    self.assertEqual(len(open_ticket_list), 2)

    self.login()
    upgrade_decision.plan()
    upgrade_decision.immediateReindexObject()
    self.login(person.getUserId())

    open_ticket_list = self.portal.Base_getEventList()
    self.assertEqual(len(open_ticket_list), 2)

    self.login()
    upgrade_decision.confirm()
    upgrade_decision.immediateReindexObject()
    self.login(person.getUserId())

    open_ticket_list = self.portal.Base_getEventList()
    self.assertEqual(len(open_ticket_list), 3)
    self.assertNotEqual(open_ticket_list[0].pubDate, None)
    self.assertEqual(open_ticket_list[0].guid,
      '{}-{}'.format(event_ud.getFollowUp(),
                     event_ud.getRelativeUrl()))

    self.login()
    upgrade_decision.start()
    upgrade_decision.immediateReindexObject()
    self.login(person.getUserId())

    open_ticket_list = self.portal.Base_getEventList()
    self.assertEqual(len(open_ticket_list), 3)
    self.assertNotEqual(open_ticket_list[0].pubDate, None)
    self.assertEqual(open_ticket_list[0].guid,
      '{}-{}'.format(event_ud.getFollowUp(),
                     event_ud.getRelativeUrl()))

    self.login()
    upgrade_decision.stop()
    upgrade_decision.immediateReindexObject()
    self.login(person.getUserId())

    open_ticket_list = self.portal.Base_getEventList()
    self.assertEqual(len(open_ticket_list), 3)
    self.assertNotEqual(open_ticket_list[0].pubDate, None)
    self.assertEqual(open_ticket_list[0].guid,
      '{}-{}'.format(event_ud.getFollowUp(),
                     event_ud.getRelativeUrl()))

    self.login()
    upgrade_decision.deliver()
    upgrade_decision.immediateReindexObject()
    self.login(person.getUserId())

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
  def testBase_getTicketUrl(self):
    ticket = self.portal.support_request_module.newContent(\
                      title="Test Support Request %s" % self.new_id)

    self.portal.portal_skins.changeSkin('RSS')
    self.assertIn("/#/%s" % ticket.getRelativeUrl(),
                  ticket.Base_getTicketUrl())

    self.assertIn("%s/#/" % self.portal.absolute_url(),
                  ticket.Base_getTicketUrl())

    web_site = self.portal.web_site_module.renderjs_oss
    self.assertIn("%s/#/" % web_site.absolute_url(),
                  web_site.support_request_module[ticket.getId()].Base_getTicketUrl())

    self.assertIn("/#/%s" % ticket.getRelativeUrl(),
                  web_site.support_request_module[ticket.getId()].Base_getTicketUrl())


class TestSlapOSSaleInvoiceTransaction_getRSSTitleAndDescription(TestRSSSyleSkinsMixin):

  def test(self):
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
      self.portal.web_site_module.renderjs_oss.accounting_module[invoice.getId()]
    self.assertEqual(
      invoice_via_website.SaleInvoiceTransaction_getRSSTitle(),
      "[RenderJS Runner] %s %s" % (text, invoice.getReference()))

    self.assertNotIn(
      invoice.Base_getTicketUrl(),
      invoice_via_website.SaleInvoiceTransaction_getRSSDescription())

    self.assertIn(
      invoice_via_website.Base_getTicketUrl(),
      invoice_via_website.SaleInvoiceTransaction_getRSSDescription())

    invoice.setStartDate(DateTime("02/01/2018"))
    self.assertEqual(
      invoice_via_website.SaleInvoiceTransaction_getRSSTitle(),
      "[RenderJS Runner] %s %s - (01/02/2018)" % (text, invoice.getReference()))

  
