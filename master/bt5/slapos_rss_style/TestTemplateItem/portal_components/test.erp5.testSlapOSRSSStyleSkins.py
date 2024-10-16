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

from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixinWithAbort,\
  TemporaryAlarmScript, PinnedDateTime

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

    software_product = self.portal.software_product_module.newContent(
      portal_type='Software Product',
      title='Theia IDE',
      follow_up_value=project)
    software_product.validate()
    software_product.publish()

    ticket = self.portal.upgrade_decision_module.newContent(
      portal_type='Upgrade Decision',
      title="Upgrade Decision Test %s" % self.new_id,
      reference="TESTUD-%s" % self.new_id,
      resource_value=software_product,
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
      destination_decision_value=person,
      resource='service_module/slapos_crm_acknowledgement'
     )

    ticket.Ticket_createProjectEvent(
      ticket.getTitle(), 'outgoing', 'Web Message',
      'service_module/slapos_crm_acknowledgement',
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

class TestSlapOSWebSection_getEventList(TestRSSSyleSkinsMixin):

  def assertTicketAndEvent(self, open_ticket_list, event, amount):
    self.assertEqual(len(open_ticket_list), amount)
    self.assertNotEqual(open_ticket_list[0].pubDate, None)
    self.assertEqual(open_ticket_list[0].guid,
      '{}-{}'.format(event.getFollowUp(),
                     event.getRelativeUrl()))

  def test_WebSection_getEventList_panel(self):
    self.test_WebSection_getEventList(
      web_site=self.portal.web_site_module.slapos_master_panel)

  def test_WebSection_getEventList(self, web_site=None):
    # WebSection_getEventList is already widely tested on Base_getTicketRelatedEventList
    # and Folder_getOpenTicketList, so we only tested the specific use case of 
    # all events togheter
    if web_site is None:
      web_site = self.portal

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
    self.assertTicketAndEvent(web_site.WebSection_getEventList(), event, 1)
    self.assertTicketAndEvent(web_site.WebSection_getEventList(
      user_restricted=1), event, 1)

    self.login()
    ticket.validate()
    self.tic()
    self.login(person.getUserId())

    self.portal.portal_skins.changeSkin('RSS')
    self.assertTicketAndEvent(web_site.WebSection_getEventList(), event, 1)
    self.assertTicketAndEvent(web_site.WebSection_getEventList(
      user_restricted=1), event, 1)

    self.login()
    ticket.suspend()
    self.tic()
    self.login(person.getUserId())

    self.portal.portal_skins.changeSkin('RSS')
    self.assertTicketAndEvent(web_site.WebSection_getEventList(), event, 1)
    self.assertTicketAndEvent(web_site.WebSection_getEventList(
      user_restricted=1), event, 1)

    self.login()
    ticket.invalidate()
    self.tic()
    self.login(person.getUserId())

    self.portal.portal_skins.changeSkin('RSS')
    open_ticket_list = web_site.WebSection_getEventList()
    self.assertEqual(len(open_ticket_list), 1)
    # Extra checks
    self.assertNotEqual(open_ticket_list[0].pubDate, None)
    self.assertNotEqual(open_ticket_list[0].link, None)
    self.assertIn(event.getTextContent(), open_ticket_list[0].description)
    self.assertEqual(open_ticket_list[0].guid,
      '{}-{}'.format(event.getFollowUp(),
                     event.getRelativeUrl()))
    self.assertEqual(open_ticket_list[0].title,
      '[MONITORING] %s' % ticket.getTitle())
    self.assertIn("%s/#/" % web_site.absolute_url(),
      open_ticket_list[0].link)

    # Now include a Regulatisation Request
    sleep(2)
    self.login()
    regularisation_request = self.newRegularisationRequest(person)
    self.login(person.getUserId())

    event_rr = regularisation_request.getFollowUpRelatedValue()
    self.assertNotEqual(event_rr, None)

    self.portal.portal_skins.changeSkin('RSS')
    open_ticket_list = web_site.WebSection_getEventList()
    self.assertTicketAndEvent(open_ticket_list, event_rr, 2)
    # check if previous still the same
    self.assertEqual(open_ticket_list[1].guid,
      '{}-{}'.format(event.getFollowUp(),
                     event.getRelativeUrl()))

    open_ticket_list = web_site.WebSection_getEventList(user_restricted=1)
    self.assertTicketAndEvent(open_ticket_list, event_rr, 2)
    # check if previous still the same
    self.assertEqual(open_ticket_list[1].guid,
      '{}-{}'.format(event.getFollowUp(),
                     event.getRelativeUrl()))
    self.assertIn("%s/#/" % web_site.absolute_url(),
      open_ticket_list[1].link)

    self.login()
    regularisation_request.validate()
    self.tic()
    self.login(person.getUserId())

    self.portal.portal_skins.changeSkin('RSS')
    self.assertTicketAndEvent(web_site.WebSection_getEventList(), event_rr, 2)
    self.assertTicketAndEvent(
      web_site.WebSection_getEventList(user_restricted=1), event_rr, 2)

    self.login()
    regularisation_request.suspend()
    self.tic()
    self.login(person.getUserId())

    self.portal.portal_skins.changeSkin('RSS')
    self.assertTicketAndEvent(web_site.WebSection_getEventList(), event_rr, 2)
    self.assertTicketAndEvent(
      web_site.WebSection_getEventList(user_restricted=1), event_rr, 2)

    self.login()
    regularisation_request.invalidate()
    self.tic()
    self.login(person.getUserId())

    self.portal.portal_skins.changeSkin('RSS')
    open_ticket_list = web_site.WebSection_getEventList()
    self.assertEqual(len(open_ticket_list), 2)
    # Extra checks
    self.assertNotEqual(open_ticket_list[0].pubDate, None)
    self.assertNotEqual(open_ticket_list[0].link, None)
    self.assertIn(event_rr.getTextContent(), open_ticket_list[0].description)
    self.assertEqual(open_ticket_list[0].guid,
      '{}-{}'.format(event_rr.getFollowUp(),
                     event_rr.getRelativeUrl()))
    self.assertEqual(open_ticket_list[0].title,
      '[ACKNOWLEDGEMENT] %s' % regularisation_request.getTitle())
    self.assertIn("%s/#/" % web_site.absolute_url(),
      open_ticket_list[0].link)

    # Now add one Upgrade Decision
    self.login()
    sleep(2)
    upgrade_decision = self.newUpgradeDecision(person, project, None)
    self.login(person.getUserId())

    event_ud = upgrade_decision.getFollowUpRelatedValue()
    self.assertNotEqual(event_ud, None)
    self.portal.portal_skins.changeSkin('RSS')
    open_ticket_list = web_site.WebSection_getEventList()
    self.assertEqual(len(open_ticket_list), 2)

    self.login()
    upgrade_decision.plan()
    self.tic()
    self.login(person.getUserId())

    self.portal.portal_skins.changeSkin('RSS')
    open_ticket_list = web_site.WebSection_getEventList()
    self.assertEqual(len(open_ticket_list), 2)

    self.login()
    upgrade_decision.confirm()
    self.tic()
    self.login(person.getUserId())

    self.portal.portal_skins.changeSkin('RSS')
    open_ticket_list = web_site.WebSection_getEventList()
    self.assertEqual(len(open_ticket_list), 3)
    self.assertNotEqual(open_ticket_list[0].pubDate, None)
    self.assertEqual(open_ticket_list[0].guid,
      '{}-{}'.format(event_ud.getFollowUp(),
                     event_ud.getRelativeUrl()))
    self.assertIn("%s/#/" % web_site.absolute_url(),
      open_ticket_list[0].link)

    self.login()
    upgrade_decision.start()
    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm',
                              "'disabled'", attribute='comment'):
      self.tic()
    self.login(person.getUserId())

    self.portal.portal_skins.changeSkin('RSS')
    open_ticket_list = web_site.WebSection_getEventList()
    self.assertEqual(len(open_ticket_list), 3)
    self.assertNotEqual(open_ticket_list[0].pubDate, None)
    self.assertEqual(open_ticket_list[0].guid,
      '{}-{}'.format(event_ud.getFollowUp(),
                     event_ud.getRelativeUrl()))
    self.assertIn("%s/#/" % web_site.absolute_url(),
      open_ticket_list[0].link)

    self.login()
    upgrade_decision.stop()
    self.tic()
    self.login(person.getUserId())

    self.portal.portal_skins.changeSkin('RSS')
    open_ticket_list = web_site.WebSection_getEventList()
    self.assertEqual(len(open_ticket_list), 3)
    self.assertNotEqual(open_ticket_list[0].pubDate, None)
    self.assertEqual(open_ticket_list[0].guid,
      '{}-{}'.format(event_ud.getFollowUp(),
                     event_ud.getRelativeUrl()))
    self.assertIn("%s/#/" % web_site.absolute_url(),
      open_ticket_list[0].link)

    self.login()
    upgrade_decision.deliver()
    self.tic()
    self.login(person.getUserId())

    self.portal.portal_skins.changeSkin('RSS')
    open_ticket_list = web_site.WebSection_getEventList()
    self.assertEqual(len(open_ticket_list), 3)
    self.assertNotEqual(open_ticket_list[0].pubDate, None)
    self.assertEqual(open_ticket_list[0].guid,
      '{}-{}'.format(event_ud.getFollowUp(),
                     event_ud.getRelativeUrl()))

    # check if ordering is correct.
    self.assertEqual(open_ticket_list[0].title,
      '[THEIA IDE] %s' % upgrade_decision.getTitle())

    self.assertIn("%s/#/" % web_site.absolute_url(),
      open_ticket_list[1].link)

    self.assertEqual(open_ticket_list[1].title,
      '[ACKNOWLEDGEMENT] %s' % regularisation_request.getTitle())

    self.assertIn("%s/#/" % web_site.absolute_url(),
      open_ticket_list[1].link)

    self.assertEqual(open_ticket_list[2].title,
      '[MONITORING] %s' % ticket.getTitle())

    self.assertIn("%s/#/" % web_site.absolute_url(),
      open_ticket_list[2].link)

class TestWebSection_getLegacyMessageList(TestRSSSyleSkinsMixin):

  def testWebSection_getLegacyMessageList(self):
    web_site = self.portal.web_site_module.slapos_master_panel.feed
    with PinnedDateTime(self, DateTime('2024/10/01')):
      self.portal.portal_skins.changeSkin('RSS')
      event_list = web_site.WebSection_getLegacyMessageList()

    self.assertEqual(len(event_list), 1)
    message = event_list[0]

    self.assertEqual(message.category, 'Disabled')
    self.assertEqual(message.author, 'Administrator')
    self.assertEqual('This RSS is disabled (20241001)', message.title)
    self.assertIn('This RSS feed is disabled:', message.description)
    self.assertIn('?date=20241001', message.link)

  def testWebSection_getLegacyMessageList_slapos_master_web_url(self):
    # Test instance tree legacy since we patch ComputeNode_view
    web_site = self.portal.web_site_module.slapos_master_panel.Base_createCloneDocument(batch_mode=1)
    web_site.edit(configuration_slapos_master_web_url='https://localhost/')
    with PinnedDateTime(self, DateTime('2024/10/01')):
      self.portal.portal_skins.changeSkin('RSS')
      event_list = web_site.feed.WebSection_getLegacyMessageList()

    self.assertEqual(len(event_list), 1)
    message = event_list[0]

    self.assertEqual(message.category, 'Disabled')
    self.assertEqual(message.author, 'Administrator')
    self.assertEqual('This RSS is disabled (20241001)', message.title)
    self.assertNotIn('This RSS feed is disabled:', message.description)
    self.assertIn('Please replace the url', message.description)
    self.assertIn('?date=20241001', message.link)

  def testWebSection_getLegacyMessageList_compute_node(self):
    web_site = self.portal.web_site_module.slapos_master_panel.Base_createCloneDocument(batch_mode=1)
    web_site.edit(configuration_slapos_master_web_url='https://localhost/')
    compute_node = self.portal.compute_node_module.newContent(
      portal_type='Compute Node'
    )
    with PinnedDateTime(self, DateTime('2024/10/01')):
      self.portal.portal_skins.changeSkin('RSS')
      event_list = web_site.feed.compute_node_module[
        compute_node.getId()
      ].WebSection_getLegacyMessageList()

    self.assertEqual(len(event_list), 1)
    message = event_list[0]

    self.assertEqual(message.category, 'Disabled')
    self.assertEqual(message.author, 'Administrator')
    self.assertEqual('This RSS is disabled (20241001)', message.title)
    self.assertIn('This RSS feed is disabled:', message.description)
    self.assertIn('?date=20241001', message.link)
    
  def testWebSection_getLegacyMessageList_instance_tree(self):
    # Test instance tree legacy since we patch InstanceTree_view
    web_site = self.portal.web_site_module.slapos_master_panel.Base_createCloneDocument(batch_mode=1)
    web_site.edit(configuration_slapos_master_web_url='https://localhost/')
    instance_tree = self.portal.instance_tree_module.newContent(
      portal_type='Instance Tree'
    )
    with PinnedDateTime(self, DateTime('2024/10/01')):
      self.portal.portal_skins.changeSkin('RSS')
      event_list = web_site.feed.instance_tree_module[
        instance_tree.getId()
      ].WebSection_getLegacyMessageList()


    self.assertEqual(len(event_list), 1)
    message = event_list[0]

    self.assertEqual(message.category, 'Disabled')
    self.assertEqual(message.author, 'Administrator')
    self.assertEqual('This RSS is disabled (20241001)', message.title)
    self.assertIn('This RSS feed is disabled:', message.description)
    self.assertIn('?date=20241001', message.link)    
  
     
    


    