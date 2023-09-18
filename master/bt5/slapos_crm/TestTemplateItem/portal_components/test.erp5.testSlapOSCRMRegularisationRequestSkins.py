# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (C) 2019  Nexedi SA and Contributors.
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
from zExceptions import Unauthorized
from DateTime import DateTime
import difflib

class TestSlapOSPerson_checkToCreateRegularisationRequest(SlapOSTestCaseMixinWithAbort):

  @simulate('NotificationTool_getDocumentValue',
            'reference=None, language="en"',
  'assert reference == "slapos-crm.create.regularisation.request"\n' \
  'return')
  @simulate('Entity_statOutstandingAmount', '*args, **kwargs', 'return "1"')
  def test_addRegularisationRequest_payment_requested(self):
    for preference in \
      self.portal.portal_catalog(portal_type="System Preference"):
      preference = preference.getObject()
      if preference.getPreferenceState() == 'global':
        preference.setPreferredSlaposWebSiteUrl('http://foobar.org/')

    person = self.makePerson(index=0, user=0)
    before_date = DateTime()
    ticket, event = person.Person_checkToCreateRegularisationRequest()
    after_date = DateTime()
    self.assertEqual(ticket.getPortalType(), 'Regularisation Request')
    self.assertEqual(ticket.getSimulationState(), 'suspended')
    self.assertEqual(ticket.getSourceProject(), person.getRelativeUrl())
    self.assertEqual(ticket.getResource(),
                      'service_module/slapos_crm_acknowledgement')
    self.assertEqual(ticket.getTitle(),
           'Account regularisation expected for "%s"' % person.getTitle())
    self.assertEqual(ticket.getDestination(),
                      person.getRelativeUrl())
    self.assertEqual(ticket.getDestinationDecision(),
                      person.getRelativeUrl())
    self.assertEqual(event.getPortalType(), 'Mail Message')
    self.assertEqual(event.getResource(),
                      'service_module/slapos_crm_acknowledgement')
    self.assertTrue(event.getStartDate() >= before_date)
    self.assertTrue(event.getStopDate() <= after_date)
    self.assertEqual(event.getTitle(), "Invoice payment requested")
    self.assertEqual(event.getDestination(),
                      person.getRelativeUrl())
    self.assertEqual(event.getSource(),
                      ticket.getSource())
    expected_text_content = """Dear Member Template,

A new invoice has been generated. 
You can access it in your invoice section at http://foobar.org/.

Regards,
The slapos team
"""
    self.assertEqual(event.getTextContent(), expected_text_content,
                      '\n'.join([x for x in difflib.unified_diff(
                                           event.getTextContent().splitlines(),
                                           expected_text_content.splitlines())]))
    self.assertEqual(event.getSimulationState(), 'delivered')

  @simulate('NotificationTool_getDocumentValue',
            'reference=None, language="en"',
  'assert reference == "slapos-crm.create.regularisation.request"\n' \
  'return context.restrictedTraverse(' \
  'context.REQUEST["test_addRegularisationRequest_notification_message"])')
  @simulate('Entity_statOutstandingAmount', '*args, **kwargs', 'return "1"')
  def test_addRegularisationRequest_notification_message(self):
    for preference in \
      self.portal.portal_catalog(portal_type="System Preference"):
      preference = preference.getObject()
      if preference.getPreferenceState() == 'global':
        preference.setPreferredSlaposWebSiteUrl('http://foobar.org/')

    person = self.makePerson(index=0, user=0)
    new_id = self.generateNewId()
    notification_message = self.portal.notification_message_module.newContent(
      portal_type="Notification Message",
      title='Test NM title %s' % new_id,
      text_content='Test NM content\n%s\n' % new_id,
      content_type='text/plain',
      )
    self.portal.REQUEST\
        ['test_addRegularisationRequest_notification_message'] = \
        notification_message.getRelativeUrl()

    before_date = DateTime()
    ticket, event = person.Person_checkToCreateRegularisationRequest()
    after_date = DateTime()
    self.assertEqual(ticket.getPortalType(), 'Regularisation Request')
    self.assertEqual(ticket.getSimulationState(), 'suspended')
    self.assertEqual(ticket.getSourceProject(), person.getRelativeUrl())
    self.assertEqual(ticket.getResource(),
                      'service_module/slapos_crm_acknowledgement')
    self.assertEqual(ticket.getTitle(),
           'Account regularisation expected for "%s"' % person.getTitle())
    self.assertEqual(ticket.getDestination(),
                      person.getRelativeUrl())
    self.assertEqual(ticket.getDestinationDecision(),
                      person.getRelativeUrl())
    self.assertEqual(event.getPortalType(), 'Mail Message')
    self.assertEqual(event.getResource(),
                      'service_module/slapos_crm_acknowledgement')
    self.assertTrue(event.getStartDate() >= before_date)
    self.assertTrue(event.getStopDate() <= after_date)
    self.assertEqual(event.getTitle(),
           'Test NM title %s' % new_id)
    self.assertEqual(event.getDestination(),
                      person.getRelativeUrl())
    self.assertEqual(event.getSource(),
                      ticket.getSource())
    expected_text_content = 'Test NM content\n%s\n' % new_id
    self.assertEqual(event.getTextContent(), expected_text_content,
                      '\n'.join([x for x in difflib.unified_diff(
                                           event.getTextContent().splitlines(),
                                           expected_text_content.splitlines())]))
    self.assertEqual(event.getSimulationState(), 'delivered')


#   def test_addRegularisationRequest_do_not_duplicate_ticket(self):
#     person = self.createPerson()
#     ticket = person.Person_checkToCreateRegularisationRequest()
#     ticket2 = person.Person_checkToCreateRegularisationRequest()
#     self.assertEqual(ticket.getRelativeUrl(), ticket2.getRelativeUrl())

  @simulate('Entity_statOutstandingAmount', '*args, **kwargs', 'return "1"')
  def test_addRegularisationRequest_do_not_duplicate_ticket_if_not_reindexed(self):
    person = self.makePerson(index=0, user=0)
    ticket, event = person.Person_checkToCreateRegularisationRequest()
    transaction.commit()
    ticket2, event2 = person.Person_checkToCreateRegularisationRequest()
    self.assertNotEqual(ticket, None)
    self.assertNotEqual(event, None)
    self.assertEqual(ticket2, None)
    self.assertEqual(event2, None)

  @simulate('Entity_statOutstandingAmount', '*args, **kwargs', 'return "0"')
  @simulate('RegularisationRequest_checkToSendUniqEvent',
            '*args, **kwargs',
            'raise NotImplementedError, "Should not have been called"')
  def test_addRegularisationRequest_balance_ok(self):
    person = self.makePerson(index=0, user=0)
    ticket, event = person.Person_checkToCreateRegularisationRequest()
    self.assertEqual(ticket, None)
    self.assertEqual(event, None)

  @simulate('Entity_statOutstandingAmount', '*args, **kwargs', 'return "1"')
  def test_addRegularisationRequest_existing_suspended_ticket(self):
    person = self.makePerson(index=0, user=0)
    ticket, event = person.Person_checkToCreateRegularisationRequest()
    transaction.commit()
    self.tic()
    ticket2, event2 = person.Person_checkToCreateRegularisationRequest()
    self.assertNotEqual(ticket, None)
    self.assertNotEqual(event, None)
    self.assertEqual(ticket2.getRelativeUrl(), ticket.getRelativeUrl())
    self.assertEqual(event2, None)

  @simulate('Entity_statOutstandingAmount', '*args, **kwargs', 'return "1"')
  def test_addRegularisationRequest_existing_validated_ticket(self):
    person = self.makePerson(index=0, user=0)
    ticket, event = person.Person_checkToCreateRegularisationRequest()
    ticket.validate()
    transaction.commit()
    self.tic()
    ticket2, event2 = person.Person_checkToCreateRegularisationRequest()
    self.assertNotEqual(ticket, None)
    self.assertNotEqual(event, None)
    self.assertEqual(ticket2.getRelativeUrl(), ticket.getRelativeUrl())
    self.assertEqual(event2, None)

  @simulate('Entity_statOutstandingAmount', '*args, **kwargs', 'return "1"')
  def test_addRegularisationRequest_existing_invalidated_ticket(self):
    person = self.makePerson(index=0, user=0)
    ticket = person.Person_checkToCreateRegularisationRequest()[0]
    ticket.invalidate()
    transaction.commit()
    self.tic()
    ticket2, event2 = person.Person_checkToCreateRegularisationRequest()
    self.assertNotEqual(ticket2.getRelativeUrl(), ticket.getRelativeUrl())
    self.assertNotEqual(event2, None)

  def test_addRegularisationRequest_REQUEST_disallowed(self):
    person = self.makePerson(index=0, user=0)
    self.assertRaises(
      Unauthorized,
      person.Person_checkToCreateRegularisationRequest,
      REQUEST={})


class TestSlapOSRegularisationRequest_invalidateIfPersonBalanceIsOk(
                                                         SlapOSTestCaseMixinWithAbort):

  def createRegularisationRequest(self):
    new_id = self.generateNewId()
    return self.portal.regularisation_request_module.newContent(
      portal_type='Regularisation Request',
      title="Test Reg. Req.%s" % new_id,
      reference="TESTREGREQ-%s" % new_id,
      )

  def test_invalidateIfPersonBalanceIsOk_REQUEST_disallowed(self):
    ticket = self.createRegularisationRequest()
    self.assertRaises(
      Unauthorized,
      ticket.RegularisationRequest_invalidateIfPersonBalanceIsOk,
      REQUEST={})

  @simulate('Entity_statOutstandingAmount', '*args, **kwargs', 'return "0"')
  def test_invalidateIfPersonBalanceIsOk_matching_case(self):
    person = self.makePerson(index=0, user=0)
    ticket = self.createRegularisationRequest()
    ticket.edit(source_project_value=person)
    ticket.validate()
    ticket.suspend()
    ticket.RegularisationRequest_invalidateIfPersonBalanceIsOk()
    self.assertEqual(ticket.getSimulationState(), 'invalidated')

  @simulate('Entity_statOutstandingAmount', '*args, **kwargs', 'return "0"')
  def test_invalidateIfPersonBalanceIsOk_validated(self):
    person = self.makePerson(index=0, user=0)
    ticket = self.createRegularisationRequest()
    ticket.edit(source_project_value=person)
    ticket.validate()
    ticket.RegularisationRequest_invalidateIfPersonBalanceIsOk()
    self.assertEqual(ticket.getSimulationState(), 'invalidated')

  @simulate('Entity_statOutstandingAmount', '*args, **kwargs', 'return "0"')
  def test_invalidateIfPersonBalanceIsOk_no_person(self):
    ticket = self.createRegularisationRequest()
    ticket.validate()
    ticket.suspend()
    ticket.RegularisationRequest_invalidateIfPersonBalanceIsOk()
    self.assertEqual(ticket.getSimulationState(), 'suspended')

  @simulate('Entity_statOutstandingAmount', '*args, **kwargs', 'return "1"')
  def test_invalidateIfPersonBalanceIsOk_wrong_balance(self):
    person = self.makePerson(index=0, user=0)
    ticket = self.createRegularisationRequest()
    ticket.edit(source_project_value=person)
    ticket.validate()
    ticket.suspend()
    ticket.RegularisationRequest_invalidateIfPersonBalanceIsOk()
    self.assertEqual(ticket.getSimulationState(), 'suspended')

class TestSlapOSRegularisationRequest_checkToSendUniqEvent(SlapOSTestCaseMixin):

  def createRegularisationRequest(self):
    new_id = self.generateNewId()
    return self.portal.regularisation_request_module.newContent(
      portal_type='Regularisation Request',
      title="Test Reg. Req.%s" % new_id,
      reference="TESTREGREQ-%s" % new_id,
      resource='foo/bar',
      )

  def test_checkToSendUniqEvent_no_event(self):
    person = self.makePerson(index=0, user=0)
    ticket = self.createRegularisationRequest()
    ticket.edit(
      source=self.expected_slapos_organisation,
      destination_value=person,
      source_project_value=person)
    ticket.validate()
    ticket.suspend()
    before_date = DateTime()
    event = ticket.RegularisationRequest_checkToSendUniqEvent(
      'service_module/slapos_crm_spam', 'foo title', 'foo content', 'foo comment')
    after_date = DateTime()

    self.assertEqual(ticket.getSimulationState(), 'suspended')
    self.assertEqual(ticket.getResource(), 'service_module/slapos_crm_spam')

    self.assertEqual(event.getPortalType(), 'Mail Message')
    self.assertEqual(event.getSimulationState(), 'delivered')
    self.assertTrue(event.getStartDate() >= before_date)
    self.assertTrue(event.getStopDate() <= after_date)
    self.assertEqual(event.getTitle(), "foo title")
    self.assertEqual(event.getResource(), 'service_module/slapos_crm_spam')
    self.assertEqual(event.getFollowUp(), ticket.getRelativeUrl())
    self.assertEqual(event.getSource(), self.expected_slapos_organisation)
    self.assertEqual(event.getDestination(), person.getRelativeUrl())
    self.assertEqual(event.getTextContent(), 'foo content')

  def test_checkToSendUniqEvent_service_required(self):
    ticket = self.createRegularisationRequest()
    self.assertRaises(
      AssertionError,
      ticket.RegularisationRequest_checkToSendUniqEvent,
      ticket.getRelativeUrl(), '', '', ''
      )

  def test_checkToSendUniqEvent_call_twice_with_tic(self):
    person = self.makePerson(index=0, user=0)
    ticket = self.createRegularisationRequest()
    ticket.edit(
      source=self.expected_slapos_organisation,
      destination_value=person,
      source_project_value=person)
    ticket.validate()
    ticket.suspend()
    event = ticket.RegularisationRequest_checkToSendUniqEvent(
      'service_module/slapos_crm_spam', 'foo title', 'foo content', 'foo comment')
    self.tic()

    event2 = ticket.RegularisationRequest_checkToSendUniqEvent(
      'service_module/slapos_crm_spam', 'foo2 title', 'foo2 content', 'foo2 comment')
    self.assertEqual(event.getTitle(), "foo title")
    self.assertEqual(event.getTextContent(), 'foo content')
    self.assertEqual(event.getRelativeUrl(), event2.getRelativeUrl())

  def test_checkToSendUniqEvent_manual_event(self):
    person = self.makePerson(index=0, user=0)
    ticket = self.createRegularisationRequest()
    ticket.edit(
      source=self.expected_slapos_organisation,
      destination_value=person,
      source_project_value=person)
    ticket.validate()
    ticket.suspend()
    event = self.portal.event_module.newContent(
      portal_type="Mail Message",
      follow_up=ticket.getRelativeUrl(),
      resource='service_module/slapos_crm_spam',
      )
    self.tic()

    event2 = ticket.RegularisationRequest_checkToSendUniqEvent(
      'service_module/slapos_crm_spam', 'foo2 title', 'foo2 content', 'foo2 comment')

    self.assertEqual(ticket.getResource(), 'foo/bar')
    self.assertNotEqual(event.getTitle(), 'foo2 title')
    self.assertEqual(event.getTextContent(), None)
    self.assertEqual(event.getSimulationState(), 'draft')
    self.assertEqual(event.getRelativeUrl(), event2.getRelativeUrl())

  def test_checkToSendUniqEvent_not_suspended(self):
    person = self.makePerson(index=0, user=0)
    ticket = self.createRegularisationRequest()
    ticket.edit(
      source=self.expected_slapos_organisation,
      destination_value=person,
      source_project_value=person)
    ticket.validate()

    event = ticket.RegularisationRequest_checkToSendUniqEvent(
      'service_module/slapos_crm_spam', 'foo2 title', 'foo2 content', 'foo2 comment')
    self.assertEqual(event, None)

  def test_checkToSendUniqEvent_event_not_reindexed(self):
    person = self.makePerson(index=0, user=0)
    ticket = self.createRegularisationRequest()
    ticket.edit(
      source=self.expected_slapos_organisation,
      destination_value=person,
      source_project_value=person)
    ticket.validate()
    ticket.suspend()
    event = ticket.RegularisationRequest_checkToSendUniqEvent(
      'service_module/slapos_crm_spam', 'foo title', 'foo content', 'foo comment')
    transaction.commit()
    event2 = ticket.RegularisationRequest_checkToSendUniqEvent(
      'service_module/slapos_crm_spam', 'foo2 title', 'foo2 content', 'foo2 comment')
    self.assertNotEqual(event, event2)
    self.assertEqual(event2, None)

  def test_checkToSendUniqEvent_REQUEST_disallowed(self):
    ticket = self.createRegularisationRequest()
    self.assertRaises(
      Unauthorized,
      ticket.RegularisationRequest_checkToSendUniqEvent,
      '', '', '', '',
      REQUEST={})

class TestSlapOSRegularisationRequest_checkToTriggerNextEscalationStep(
                                                          SlapOSTestCaseMixinWithAbort):

  def createRegularisationRequest(self):
    new_id = self.generateNewId()
    return self.portal.regularisation_request_module.newContent(
      portal_type='Regularisation Request',
      title="Test Reg. Req.%s" % new_id,
      reference="TESTREGREQ-%s" % new_id,
      resource='foo/bar',
      )

  def test_checkToTriggerNextEscalationStep_service_required(self):
    ticket = self.createRegularisationRequest()
    self.assertRaises(
      AssertionError,
      ticket.RegularisationRequest_checkToTriggerNextEscalationStep,
      0, ticket.getRelativeUrl(), '', '', '', ''
      )

  @simulate('NotificationTool_getDocumentValue',
            'reference=None, language="en"',
  'assert reference == "slapos-crm.acknowledgment.escalation", reference\n' \
  'return')
  @simulate('RegularisationRequest_checkToSendUniqEvent',
            'service_relative_url, title, text_content, comment, REQUEST=None',
  'context.portal_workflow.doActionFor(' \
  'context, action="edit_action", ' \
  'comment="Visited by RegularisationRequest_checkToSendUniqEvent ' \
  '%s %s %s %s" % (service_relative_url, title, text_content, comment))\n' \
  'return "fooevent"')
  def test_checkToTriggerNextEscalationStep_matching_event(self):
    ticket = self.createRegularisationRequest()
    ticket.edit(resource='service_module/slapos_crm_acknowledgement')
    ticket.validate()
    ticket.suspend()
    event = self.portal.event_module.newContent(
      portal_type="Mail Message",
      follow_up=ticket.getRelativeUrl(),
      resource='service_module/slapos_crm_acknowledgement',
      start_date=DateTime() - 8,
      )
    self.portal.portal_workflow._jumpToStateFor(event, 'delivered')
    self.tic()

    event2 = ticket.RegularisationRequest_checkToTriggerNextEscalationStep(
        7, 'service_module/slapos_crm_acknowledgement',
        'service_module/slapos_crm_spam',
        'foo2 title', 'foo2 content', 'foo2 comment')

    self.assertEqual(event2, event.getRelativeUrl())
    self.assertEqual(
      'Visited by RegularisationRequest_checkToSendUniqEvent %s %s %s %s' % \
      ('service_module/slapos_crm_spam', 'foo2 title', 'foo2 content',
       'foo2 comment'),
      ticket.workflow_history['edit_workflow'][-1]['comment'])

  @simulate('RegularisationRequest_checkToSendUniqEvent',
            '*args, **kwargs',
            'raise NotImplementedError, "Should not have been called"')
  def test_checkToTriggerNextEscalationStep_recent_event(self):
    ticket = self.createRegularisationRequest()
    ticket.edit(resource='service_module/slapos_crm_acknowledgement')
    ticket.validate()
    ticket.suspend()
    event = self.portal.event_module.newContent(
      portal_type="Mail Message",
      follow_up=ticket.getRelativeUrl(),
      resource='service_module/slapos_crm_acknowledgement',
      start_date=DateTime() - 6,
      )
    self.portal.portal_workflow._jumpToStateFor(event, 'delivered')
    self.tic()

    event2 = ticket.RegularisationRequest_checkToTriggerNextEscalationStep(
        7, 'service_module/slapos_crm_acknowledgement',
        'service_module/slapos_crm_spam',
        'foo2 title', 'foo2 content', 'foo2 comment')

    self.assertEqual(event2, None)

  @simulate('RegularisationRequest_checkToSendUniqEvent',
            '*args, **kwargs',
            'raise NotImplementedError, "Should not have been called"')
  def test_checkToTriggerNextEscalationStep_other_ticket_event(self):
    ticket = self.createRegularisationRequest()
    ticket.edit(resource='service_module/slapos_crm_acknowledgement')
    ticket.validate()
    ticket.suspend()
    event = self.portal.event_module.newContent(
      portal_type="Mail Message",
      resource='service_module/slapos_crm_acknowledgement',
      start_date=DateTime() - 2,
      )
    self.portal.portal_workflow._jumpToStateFor(event, 'delivered')
    self.tic()

    event2 = ticket.RegularisationRequest_checkToTriggerNextEscalationStep(
        1, 'service_module/slapos_crm_acknowledgement',
        'service_module/slapos_crm_spam',
        'foo2 title', 'foo2 content', 'foo2 comment')

    self.assertEqual(event2, None)

  @simulate('RegularisationRequest_checkToSendUniqEvent',
            '*args, **kwargs',
            'raise NotImplementedError, "Should not have been called"')
  def test_checkToTriggerNextEscalationStep_other_resource_event(self):
    ticket = self.createRegularisationRequest()
    ticket.edit(resource='service_module/slapos_crm_acknowledgement')
    ticket.validate()
    ticket.suspend()
    event = self.portal.event_module.newContent(
      portal_type="Mail Message",
      follow_up=ticket.getRelativeUrl(),
      resource='service_module/slapos_crm_spam',
      start_date=DateTime() - 2,
      )
    self.portal.portal_workflow._jumpToStateFor(event, 'delivered')
    self.tic()

    event2 = ticket.RegularisationRequest_checkToTriggerNextEscalationStep(
        1, 'service_module/slapos_crm_acknowledgement',
        'service_module/slapos_crm_spam',
        'foo2 title', 'foo2 content', 'foo2 comment')

    self.assertEqual(event2, None)

  @simulate('RegularisationRequest_checkToSendUniqEvent',
            '*args, **kwargs',
            'raise NotImplementedError, "Should not have been called"')
  def test_checkToTriggerNextEscalationStep_no_current_event(self):
    ticket = self.createRegularisationRequest()
    ticket.edit(resource='service_module/slapos_crm_acknowledgement')
    ticket.validate()
    ticket.suspend()
    self.tic()

    event2 = ticket.RegularisationRequest_checkToTriggerNextEscalationStep(
        1, 'service_module/slapos_crm_acknowledgement',
        'service_module/slapos_crm_spam',
        'foo2 title', 'foo2 content', 'foo2 comment')

    self.assertEqual(event2, None)

  @simulate('RegularisationRequest_checkToSendUniqEvent',
            '*args, **kwargs',
            'raise NotImplementedError, "Should not have been called"')
  def test_checkToTriggerNextEscalationStep_no_ticket_resource(self):
    ticket = self.createRegularisationRequest()
    ticket.validate()
    ticket.suspend()
    event = self.portal.event_module.newContent(
      portal_type="Mail Message",
      follow_up=ticket.getRelativeUrl(),
      resource='service_module/slapos_crm_acknowledgement',
      start_date=DateTime() - 2,
      )
    self.portal.portal_workflow._jumpToStateFor(event, 'delivered')
    self.tic()

    event2 = ticket.RegularisationRequest_checkToTriggerNextEscalationStep(
        1, 'service_module/slapos_crm_acknowledgement',
        'service_module/slapos_crm_spam',
        'foo2 title', 'foo2 content', 'foo2 comment')

    self.assertEqual(event2, None)

  @simulate('RegularisationRequest_checkToSendUniqEvent',
            '*args, **kwargs',
            'raise NotImplementedError, "Should not have been called"')
  def test_checkToTriggerNextEscalationStep_not_suspended(self):
    ticket = self.createRegularisationRequest()
    ticket.edit(resource='service_module/slapos_crm_acknowledgement')
    ticket.validate()
    event = self.portal.event_module.newContent(
      portal_type="Mail Message",
      follow_up=ticket.getRelativeUrl(),
      resource='service_module/slapos_crm_acknowledgement',
      start_date=DateTime() - 2,
      )
    self.portal.portal_workflow._jumpToStateFor(event, 'delivered')
    self.tic()

    event2 = ticket.RegularisationRequest_checkToTriggerNextEscalationStep(
        1, 'service_module/slapos_crm_acknowledgement',
        'service_module/slapos_crm_spam',
        'foo2 title', 'foo2 content', 'foo2 comment')

    self.assertEqual(event2, None)

  def test_checkToTriggerNextEscalationStep_REQUEST_disallowed(self):
    ticket = self.createRegularisationRequest()
    self.assertRaises(
      Unauthorized,
      ticket.RegularisationRequest_checkToTriggerNextEscalationStep,
      '', '', '', '', '', '',
      REQUEST={})

class TestSlapOSRegularisationRequest_triggerAcknowledgmentEscalation(
                                                          SlapOSTestCaseMixinWithAbort):

  def test_triggerAcknowledgmentEscalation_REQUEST_disallowed(self):
    ticket = self.createRegularisationRequest()
    self.assertRaises(
      Unauthorized,
      ticket.RegularisationRequest_triggerAcknowledgmentEscalation,
      REQUEST={})

  @simulate('NotificationTool_getDocumentValue',
            'reference=None, language="en"',
  'assert reference == "slapos-crm.acknowledgment.escalation", reference\n' \
  'return')
  @simulate('RegularisationRequest_checkToTriggerNextEscalationStep',
            'delay_period_in_days, current_service_relative_url, next_service_relative_url, title, text_content, comment, REQUEST=None',
  'context.portal_workflow.doActionFor(' \
  'context, action="edit_action", ' \
  'comment="Visited by RegularisationRequest_checkToTriggerNextEscalationStep ' \
  '%s %s %s %s %s %s" % (delay_period_in_days, current_service_relative_url, next_service_relative_url, title, text_content, comment))')
  def test_checkToTriggerNextEscalationStep_matching_event(self):
    ticket = self.createRegularisationRequest()
    ticket.RegularisationRequest_triggerAcknowledgmentEscalation()
    self.assertEqual(
      'Visited by RegularisationRequest_checkToTriggerNextEscalationStep ' \
      '%s %s %s %s %s %s' % \
      (15,
       'service_module/slapos_crm_acknowledgement',
       'service_module/slapos_crm_stop_reminder',
       'Reminder: invoice payment requested',
"""Dear user,

We would like to remind you the unpaid invoice you have on %s.
If no payment is done during the coming days, we will stop all your current instances to free some hardware resources.

Regards,
The slapos team
""" % self.portal.portal_preferences.getPreferredSlaposWebSiteUrl(),
       'Stopping reminder.'),
      ticket.workflow_history['edit_workflow'][-1]['comment'])

  @simulate('NotificationTool_getDocumentValue',
            'reference=None, language="en"',
  'assert reference == "slapos-crm.acknowledgment.escalation"\n' \
  'return context.restrictedTraverse(' \
  'context.REQUEST["test_checkToTriggerNextEscalationStep_notification_message"])')
  @simulate('RegularisationRequest_checkToTriggerNextEscalationStep',
            'delay_period_in_days, current_service_relative_url, next_service_relative_url, title, text_content, comment, REQUEST=None',
  'context.portal_workflow.doActionFor(' \
  'context, action="edit_action", ' \
  'comment="Visited by RegularisationRequest_checkToTriggerNextEscalationStep ' \
  '%s %s %s %s %s %s" % (delay_period_in_days, current_service_relative_url, next_service_relative_url, title, text_content, comment))')
  def test_checkToTriggerNextEscalationStep_notification_message(self):
    ticket = self.createRegularisationRequest()
    new_id = self.generateNewId()
    notification_message = self.portal.notification_message_module.newContent(
      portal_type="Notification Message",
      title='Test NM title %s' % new_id,
      text_content='Test NM content\n%s\n' % new_id,
      content_type='text/plain',
      )
    self.portal.REQUEST\
        ['test_checkToTriggerNextEscalationStep_notification_message'] = \
        notification_message.getRelativeUrl()
    ticket.RegularisationRequest_triggerAcknowledgmentEscalation()
    self.assertEqual(
      'Visited by RegularisationRequest_checkToTriggerNextEscalationStep ' \
      '%s %s %s %s %s %s' % \
      (15,
       'service_module/slapos_crm_acknowledgement',
       'service_module/slapos_crm_stop_reminder',
       'Test NM title %s' % new_id,
       'Test NM content\n%s\n' % new_id,
       'Stopping reminder.'),
      ticket.workflow_history['edit_workflow'][-1]['comment'])

class TestSlapOSRegularisationRequest_triggerStopReminderEscalation(
                                                          SlapOSTestCaseMixinWithAbort):

  def test_triggerStopReminderEscalation_REQUEST_disallowed(self):
    ticket = self.createRegularisationRequest()
    self.assertRaises(
      Unauthorized,
      ticket.RegularisationRequest_triggerStopReminderEscalation,
      REQUEST={})

  @simulate('NotificationTool_getDocumentValue',
            'reference=None, language="en"',
  'assert reference == "slapos-crm.stop.reminder.escalation", reference\n' \
  'return')
  @simulate('RegularisationRequest_checkToTriggerNextEscalationStep',
            'delay_period_in_days, current_service_relative_url, next_service_relative_url, title, text_content, comment, REQUEST=None',
  'context.portal_workflow.doActionFor(' \
  'context, action="edit_action", ' \
  'comment="Visited by RegularisationRequest_checkToTriggerNextEscalationStep ' \
  '%s %s %s %s %s %s" % (delay_period_in_days, current_service_relative_url, next_service_relative_url, title, text_content, comment))')
  def test_checkToTriggerNextEscalationStep_matching_event(self):
    ticket = self.createRegularisationRequest()
    ticket.RegularisationRequest_triggerStopReminderEscalation()
    self.assertEqual(
      'Visited by RegularisationRequest_checkToTriggerNextEscalationStep ' \
      '%s %s %s %s %s %s' % \
      (7,
       'service_module/slapos_crm_stop_reminder',
       'service_module/slapos_crm_stop_acknowledgement',
       'Acknowledgment: instances stopped',
"""Dear user,

Despite our last reminder, you still have an unpaid invoice on %s.
We will now stop all your current instances to free some hardware resources.

Regards,
The slapos team
""" % self.portal.portal_preferences.getPreferredSlaposWebSiteUrl(),
       'Stopping acknowledgment.'),
      ticket.workflow_history['edit_workflow'][-1]['comment'])

  @simulate('NotificationTool_getDocumentValue',
            'reference=None, language="en"',
  'assert reference == "slapos-crm.stop.reminder.escalation"\n' \
  'return context.restrictedTraverse(' \
  'context.REQUEST["test_checkToTriggerNextEscalationStep_notification_message"])')
  @simulate('RegularisationRequest_checkToTriggerNextEscalationStep',
            'delay_period_in_days, current_service_relative_url, next_service_relative_url, title, text_content, comment, REQUEST=None',
  'context.portal_workflow.doActionFor(' \
  'context, action="edit_action", ' \
  'comment="Visited by RegularisationRequest_checkToTriggerNextEscalationStep ' \
  '%s %s %s %s %s %s" % (delay_period_in_days, current_service_relative_url, next_service_relative_url, title, text_content, comment))')
  def test_checkToTriggerNextEscalationStep_notification_message(self):
    ticket = self.createRegularisationRequest()
    new_id = self.generateNewId()
    notification_message = self.portal.notification_message_module.newContent(
      portal_type="Notification Message",
      title='Test NM title %s' % new_id,
      text_content='Test NM content\n%s\n' % new_id,
      content_type='text/plain',
      )
    self.portal.REQUEST\
        ['test_checkToTriggerNextEscalationStep_notification_message'] = \
        notification_message.getRelativeUrl()
    ticket.RegularisationRequest_triggerStopReminderEscalation()
    self.assertEqual(
      'Visited by RegularisationRequest_checkToTriggerNextEscalationStep ' \
      '%s %s %s %s %s %s' % \
      (7,
       'service_module/slapos_crm_stop_reminder',
       'service_module/slapos_crm_stop_acknowledgement',
       'Test NM title %s' % new_id,
       'Test NM content\n%s\n' % new_id,
       'Stopping acknowledgment.'),
      ticket.workflow_history['edit_workflow'][-1]['comment'])

class TestSlapOSRegularisationRequest_triggerStopAcknowledgmentEscalation(
                                                          SlapOSTestCaseMixinWithAbort):

  def test_triggerStopAcknowledgmentEscalation_REQUEST_disallowed(self):
    ticket = self.createRegularisationRequest()
    self.assertRaises(
      Unauthorized,
      ticket.RegularisationRequest_triggerStopAcknowledgmentEscalation,
      REQUEST={})

  @simulate('NotificationTool_getDocumentValue',
            'reference=None, language="en"',
  'assert reference == "slapos-crm.stop.acknowledgment.escalation", reference\n' \
  'return')
  @simulate('RegularisationRequest_checkToTriggerNextEscalationStep',
            'delay_period_in_days, current_service_relative_url, next_service_relative_url, title, text_content, comment, REQUEST=None',
  'context.portal_workflow.doActionFor(' \
  'context, action="edit_action", ' \
  'comment="Visited by RegularisationRequest_checkToTriggerNextEscalationStep ' \
  '%s %s %s %s %s %s" % (delay_period_in_days, current_service_relative_url, next_service_relative_url, title, text_content, comment))')
  def test_checkToTriggerNextEscalationStep_matching_event(self):
    ticket = self.createRegularisationRequest()
    ticket.RegularisationRequest_triggerStopAcknowledgmentEscalation()
    self.assertEqual(
      'Visited by RegularisationRequest_checkToTriggerNextEscalationStep ' \
      '%s %s %s %s %s %s' % \
      (7,
       'service_module/slapos_crm_stop_acknowledgement',
       'service_module/slapos_crm_delete_reminder',
       'Last reminder: invoice payment requested',
"""Dear user,

We would like to remind you the unpaid invoice you have on %s.
If no payment is done during the coming days, we will delete all your instances.

Regards,
The slapos team
""" % self.portal.portal_preferences.getPreferredSlaposWebSiteUrl(),
       'Deleting reminder.'),
      ticket.workflow_history['edit_workflow'][-1]['comment'])

  @simulate('NotificationTool_getDocumentValue',
            'reference=None, language="en"',
  'assert reference == "slapos-crm.stop.acknowledgment.escalation"\n' \
  'return context.restrictedTraverse(' \
  'context.REQUEST["test_checkToTriggerNextEscalationStep_notification_message"])')
  @simulate('RegularisationRequest_checkToTriggerNextEscalationStep',
            'delay_period_in_days, current_service_relative_url, next_service_relative_url, title, text_content, comment, REQUEST=None',
  'context.portal_workflow.doActionFor(' \
  'context, action="edit_action", ' \
  'comment="Visited by RegularisationRequest_checkToTriggerNextEscalationStep ' \
  '%s %s %s %s %s %s" % (delay_period_in_days, current_service_relative_url, next_service_relative_url, title, text_content, comment))')
  def test_checkToTriggerNextEscalationStep_notification_message(self):
    ticket = self.createRegularisationRequest()
    new_id = self.generateNewId()
    notification_message = self.portal.notification_message_module.newContent(
      portal_type="Notification Message",
      title='Test NM title %s' % new_id,
      text_content='Test NM content\n%s\n' % new_id,
      content_type='text/plain',
      )
    self.portal.REQUEST\
        ['test_checkToTriggerNextEscalationStep_notification_message'] = \
        notification_message.getRelativeUrl()
    ticket.RegularisationRequest_triggerStopAcknowledgmentEscalation()
    self.assertEqual(
      'Visited by RegularisationRequest_checkToTriggerNextEscalationStep ' \
      '%s %s %s %s %s %s' % \
      (7,
       'service_module/slapos_crm_stop_acknowledgement',
       'service_module/slapos_crm_delete_reminder',
       'Test NM title %s' % new_id,
       'Test NM content\n%s\n' % new_id,
       'Deleting reminder.'),
      ticket.workflow_history['edit_workflow'][-1]['comment'])

class TestSlapOSRegularisationRequest_triggerDeleteReminderEscalation(
                                                          SlapOSTestCaseMixinWithAbort):

  def test_triggerDeleteReminderEscalation_REQUEST_disallowed(self):
    ticket = self.createRegularisationRequest()
    self.assertRaises(
      Unauthorized,
      ticket.RegularisationRequest_triggerDeleteReminderEscalation,
      REQUEST={})

  @simulate('NotificationTool_getDocumentValue',
            'reference=None, language="en"',
  'assert reference == "slapos-crm.delete.reminder.escalation", reference\n' \
  'return')
  @simulate('RegularisationRequest_checkToTriggerNextEscalationStep',
            'delay_period_in_days, current_service_relative_url, next_service_relative_url, title, text_content, comment, REQUEST=None',
  'context.portal_workflow.doActionFor(' \
  'context, action="edit_action", ' \
  'comment="Visited by RegularisationRequest_checkToTriggerNextEscalationStep ' \
  '%s %s %s %s %s %s" % (delay_period_in_days, current_service_relative_url, next_service_relative_url, title, text_content, comment))')
  def test_checkToTriggerNextEscalationStep_matching_event(self):
    ticket = self.createRegularisationRequest()
    ticket.RegularisationRequest_triggerDeleteReminderEscalation()
    self.assertEqual(
      'Visited by RegularisationRequest_checkToTriggerNextEscalationStep ' \
      '%s %s %s %s %s %s' % \
      (10,
       'service_module/slapos_crm_delete_reminder',
       'service_module/slapos_crm_delete_acknowledgement',
       'Acknowledgment: instances deleted',
"""Dear user,

Despite our last reminder, you still have an unpaid invoice on %s.
We will now delete all your instances.

Regards,
The slapos team
""" % self.portal.portal_preferences.getPreferredSlaposWebSiteUrl(),
       'Deleting acknowledgment.'),
      ticket.workflow_history['edit_workflow'][-1]['comment'])

  @simulate('NotificationTool_getDocumentValue',
            'reference=None, language="en"',
  'assert reference == "slapos-crm.delete.reminder.escalation"\n' \
  'return context.restrictedTraverse(' \
  'context.REQUEST["test_checkToTriggerNextEscalationStep_notification_message"])')
  @simulate('RegularisationRequest_checkToTriggerNextEscalationStep',
            'delay_period_in_days, current_service_relative_url, next_service_relative_url, title, text_content, comment, REQUEST=None',
  'context.portal_workflow.doActionFor(' \
  'context, action="edit_action", ' \
  'comment="Visited by RegularisationRequest_checkToTriggerNextEscalationStep ' \
  '%s %s %s %s %s %s" % (delay_period_in_days, current_service_relative_url, next_service_relative_url, title, text_content, comment))')
  def test_checkToTriggerNextEscalationStep_notification_message(self):
    ticket = self.createRegularisationRequest()
    new_id = self.generateNewId()
    notification_message = self.portal.notification_message_module.newContent(
      portal_type="Notification Message",
      title='Test NM title %s' % new_id,
      text_content='Test NM content\n%s\n' % new_id,
      content_type='text/plain',
      )
    self.portal.REQUEST\
        ['test_checkToTriggerNextEscalationStep_notification_message'] = \
        notification_message.getRelativeUrl()
    ticket.RegularisationRequest_triggerDeleteReminderEscalation()
    self.assertEqual(
      'Visited by RegularisationRequest_checkToTriggerNextEscalationStep ' \
      '%s %s %s %s %s %s' % \
      (10,
       'service_module/slapos_crm_delete_reminder',
       'service_module/slapos_crm_delete_acknowledgement',
       'Test NM title %s' % new_id,
       'Test NM content\n%s\n' % new_id,
       'Deleting acknowledgment.'),
      ticket.workflow_history['edit_workflow'][-1]['comment'])

class TestSlapOSRegularisationRequest_stopInstanceTreeList(
                                                          SlapOSTestCaseMixinWithAbort):

  def createInstanceTree(self):
    new_id = self.generateNewId()
    instance_tree = self.portal.instance_tree_module\
        .template_instance_tree.Base_createCloneDocument(batch_mode=1)
    instance_tree.edit(
      reference="TESTHS-%s" % new_id,
    )
    instance_tree.validate()
    self.portal.portal_workflow._jumpToStateFor(
        instance_tree, 'start_requested')
    return instance_tree

  def test_stopInstanceTreeList_REQUEST_disallowed(self):
    ticket = self.createRegularisationRequest()
    self.assertRaises(
      Unauthorized,
      ticket.RegularisationRequest_stopInstanceTreeList,
      'footag',
      REQUEST={})

  @simulate('InstanceTree_stopFromRegularisationRequest',
            'person, REQUEST=None',
  'context.portal_workflow.doActionFor(' \
  'context, action="edit_action", ' \
  'comment="Visited by InstanceTree_stopFromRegularisationRequest ' \
  '%s" % (person))')
  def test_stopInstanceTreeList_matching_subscription(self):
    person = self.makePerson(index=0, user=0)
    ticket = self.createRegularisationRequest()
    instance_tree = self.createInstanceTree()

    ticket.edit(
      source_project_value=person,
      resource='service_module/slapos_crm_stop_acknowledgement',
    )
    ticket.validate()
    ticket.suspend()
    instance_tree.edit(
      destination_section=person.getRelativeUrl(),
    )
    self.tic()

    result = ticket.\
        RegularisationRequest_stopInstanceTreeList('footag')
    self.assertTrue(result)

    self.tic()
    self.assertEqual(
      'Visited by InstanceTree_stopFromRegularisationRequest ' \
      '%s' % person.getRelativeUrl(),
      instance_tree.workflow_history['edit_workflow'][-1]['comment'])

  @simulate('InstanceTree_stopFromRegularisationRequest',
            'person, REQUEST=None',
  'context.portal_workflow.doActionFor(' \
  'context, action="edit_action", ' \
  'comment="Visited by InstanceTree_stopFromRegularisationRequest ' \
  '%s" % (person))')
  def test_stopInstanceTreeList_matching_subscription_2(self):
    person = self.makePerson(index=0, user=0)
    ticket = self.createRegularisationRequest()
    instance_tree = self.createInstanceTree()

    ticket.edit(
      source_project_value=person,
      resource='service_module/slapos_crm_delete_reminder',
    )
    ticket.validate()
    ticket.suspend()
    instance_tree.edit(
      destination_section=person.getRelativeUrl(),
    )
    self.tic()

    result = ticket.\
        RegularisationRequest_stopInstanceTreeList('footag')
    self.assertTrue(result)

    self.tic()
    self.assertEqual(
      'Visited by InstanceTree_stopFromRegularisationRequest ' \
      '%s' % person.getRelativeUrl(),
      instance_tree.workflow_history['edit_workflow'][-1]['comment'])

  @simulate('InstanceTree_stopFromRegularisationRequest',
            '*args, **kwargs',
            'raise NotImplementedError, "Should not have been called"')
  def test_stopInstanceTreeList_other_subscription(self):
    person = self.makePerson(index=0, user=0)
    ticket = self.createRegularisationRequest()
    self.createInstanceTree()

    ticket.edit(
      source_project_value=person,
      resource='service_module/slapos_crm_stop_acknowledgement',
    )
    ticket.validate()
    ticket.suspend()

    self.tic()

    result = ticket.\
        RegularisationRequest_stopInstanceTreeList('footag')
    self.assertTrue(result)

    self.tic()

  @simulate('InstanceTree_stopFromRegularisationRequest',
            '*args, **kwargs',
            'raise NotImplementedError, "Should not have been called"')
  def test_stopInstanceTreeList_no_person(self):
    ticket = self.createRegularisationRequest()

    ticket.edit(
      resource='service_module/slapos_crm_stop_acknowledgement',
    )
    ticket.validate()
    ticket.suspend()

    self.tic()

    result = ticket.\
        RegularisationRequest_stopInstanceTreeList('footag')
    self.assertFalse(result)

    self.tic()

  @simulate('InstanceTree_stopFromRegularisationRequest',
            '*args, **kwargs',
            'raise NotImplementedError, "Should not have been called"')
  def test_stopInstanceTreeList_not_suspended(self):
    person = self.makePerson(index=0, user=0)
    ticket = self.createRegularisationRequest()
    self.createInstanceTree()

    ticket.edit(
      source_project_value=person,
      resource='service_module/slapos_crm_stop_acknowledgement',
    )
    ticket.validate()

    self.tic()

    result = ticket.\
        RegularisationRequest_stopInstanceTreeList('footag')
    self.assertFalse(result)

    self.tic()

  @simulate('InstanceTree_stopFromRegularisationRequest',
            '*args, **kwargs',
            'raise NotImplementedError, "Should not have been called"')
  def test_stopInstanceTreeList_other_resource(self):
    person = self.makePerson(index=0, user=0)
    ticket = self.createRegularisationRequest()
    self.createInstanceTree()

    ticket.edit(
      source_project_value=person,
      resource='service_module/slapos_crm_acknowledgement',
    )
    ticket.validate()
    ticket.suspend()

    self.tic()

    result = ticket.\
        RegularisationRequest_stopInstanceTreeList('footag')
    self.assertFalse(result)

    self.tic()

class TestSlapOSInstanceTree_stopFromRegularisationRequest(
                                                          SlapOSTestCaseMixinWithAbort):

  launch_caucase = 1
  def createInstanceTree(self):
    new_id = self.generateNewId()
    instance_tree = self.portal.instance_tree_module\
        .template_instance_tree.Base_createCloneDocument(batch_mode=1)
    instance_tree.edit(
      reference="TESTHS-%s" % new_id,
    )
    instance_tree.validate()
    self.portal.portal_workflow._jumpToStateFor(
        instance_tree, 'start_requested')
    return instance_tree

  def test_stopFromRegularisationRequest_REQUEST_disallowed(self):
    self.assertRaises(
      Unauthorized,
      self.portal.InstanceTree_stopFromRegularisationRequest,
      '',
      REQUEST={})

  def test_stopFromRegularisationRequest_matching_subscription(self):
    person = self.makePerson(index=0, user=0)
    instance_tree = self.createInstanceTree()
    instance_tree.edit(
      destination_section=person.getRelativeUrl(),
    )
    self.tic()

    software_release = instance_tree.getUrlString()
    software_title = instance_tree.getTitle()
    software_type = instance_tree.getSourceReference()
    instance_xml = instance_tree.getTextContent()
    sla_xml = instance_tree.getSlaXml()
    shared = instance_tree.isRootSlave()
    self.assertEqual(instance_tree.getSlapState(), "start_requested")

    result = instance_tree.\
        InstanceTree_stopFromRegularisationRequest(person.getRelativeUrl())

    self.assertEqual(result, True)
    self.assertEqual(instance_tree.getUrlString(), software_release)
    self.assertEqual(instance_tree.getTitle(), software_title)
    self.assertEqual(instance_tree.getSourceReference(), software_type)
    self.assertEqual(instance_tree.getTextContent(), instance_xml)
    self.assertEqual(instance_tree.getSlaXml(), sla_xml)
    self.assertEqual(instance_tree.isRootSlave(), shared)
    self.assertEqual(instance_tree.getSlapState(), "stop_requested")

  def test_stopFromRegularisationRequest_stopped_subscription(self):
    person = self.makePerson(index=0, user=0)
    instance_tree = self.createInstanceTree()
    instance_tree.edit(
      destination_section=person.getRelativeUrl(),
    )
    self.portal.portal_workflow._jumpToStateFor(
        instance_tree, 'stop_requested')

    result = instance_tree.\
        InstanceTree_stopFromRegularisationRequest(person.getRelativeUrl())

    self.assertEqual(result, False)

  def test_stopFromRegularisationRequest_non_matching_person(self):
    instance_tree = self.createInstanceTree()
    self.assertRaises(
      AssertionError,
      instance_tree.InstanceTree_stopFromRegularisationRequest,
      'foobar')

class TestSlapOSInstanceTree_deleteFromRegularisationRequest(
                                                          SlapOSTestCaseMixinWithAbort):

  def createInstanceTree(self):
    new_id = self.generateNewId()
    instance_tree = self.portal.instance_tree_module\
        .template_instance_tree.Base_createCloneDocument(batch_mode=1)
    instance_tree.edit(
      reference="TESTHS-%s" % new_id,
    )
    instance_tree.validate()
    self.portal.portal_workflow._jumpToStateFor(
        instance_tree, 'start_requested')
    return instance_tree

  def test_deleteFromRegularisationRequest_REQUEST_disallowed(self):
    self.assertRaises(
      Unauthorized,
      self.portal.InstanceTree_deleteFromRegularisationRequest,
      '',
      REQUEST={})

  def test_deleteFromRegularisationRequest_started_subscription(self):
    person = self.makePerson(index=0, user=0)
    instance_tree = self.createInstanceTree()
    instance_tree.edit(
      destination_section=person.getRelativeUrl(),
    )
    self.tic()

    software_release = instance_tree.getUrlString()
    software_title = instance_tree.getTitle()
    software_type = instance_tree.getSourceReference()
    instance_xml = instance_tree.getTextContent()
    sla_xml = instance_tree.getSlaXml()
    shared = instance_tree.isRootSlave()
    self.assertEqual(instance_tree.getSlapState(), "start_requested")

    result = instance_tree.\
        InstanceTree_deleteFromRegularisationRequest(person.getRelativeUrl())

    self.assertEqual(result, True)
    self.assertEqual(instance_tree.getUrlString(), software_release)
    self.assertEqual(instance_tree.getTitle(), software_title)
    self.assertEqual(instance_tree.getSourceReference(), software_type)
    self.assertEqual(instance_tree.getTextContent(), instance_xml)
    self.assertEqual(instance_tree.getSlaXml(), sla_xml)
    self.assertEqual(instance_tree.isRootSlave(), shared)
    self.assertEqual(instance_tree.getSlapState(), "destroy_requested")

  def test_deleteFromRegularisationRequest_stopped_subscription(self):
    person = self.makePerson(index=0, user=0)
    instance_tree = self.createInstanceTree()
    instance_tree.edit(
      destination_section=person.getRelativeUrl(),
    )
    self.portal.portal_workflow._jumpToStateFor(
        instance_tree, 'stop_requested')
    self.tic()

    software_release = instance_tree.getUrlString()
    software_title = instance_tree.getTitle()
    software_type = instance_tree.getSourceReference()
    instance_xml = instance_tree.getTextContent()
    sla_xml = instance_tree.getSlaXml()
    shared = instance_tree.isRootSlave()
    self.assertEqual(instance_tree.getSlapState(), "stop_requested")

    result = instance_tree.\
        InstanceTree_deleteFromRegularisationRequest(person.getRelativeUrl())

    self.assertEqual(result, True)
    self.assertEqual(instance_tree.getUrlString(), software_release)
    self.assertEqual(instance_tree.getTitle(), software_title)
    self.assertEqual(instance_tree.getSourceReference(), software_type)
    self.assertEqual(instance_tree.getTextContent(), instance_xml)
    self.assertEqual(instance_tree.getSlaXml(), sla_xml)
    self.assertEqual(instance_tree.isRootSlave(), shared)
    self.assertEqual(instance_tree.getSlapState(), "destroy_requested")

  def test_deleteFromRegularisationRequest_destroyed_subscription(self):
    person = self.makePerson(index=0, user=0)
    instance_tree = self.createInstanceTree()
    instance_tree.edit(
      destination_section=person.getRelativeUrl(),
    )
    self.portal.portal_workflow._jumpToStateFor(
        instance_tree, 'destroy_requested')

    result = instance_tree.\
        InstanceTree_deleteFromRegularisationRequest(person.getRelativeUrl())

    self.assertEqual(result, False)

  def test_deleteFromRegularisationRequest_non_matching_person(self):
    instance_tree = self.createInstanceTree()
    self.assertRaises(
      AssertionError,
      instance_tree.InstanceTree_deleteFromRegularisationRequest,
      'foobar')

class TestSlapOSRegularisationRequest_deleteInstanceTreeList(
                                                          SlapOSTestCaseMixinWithAbort):

  def createRegularisationRequest(self):
    new_id = self.generateNewId()
    return self.portal.regularisation_request_module.newContent(
      portal_type='Regularisation Request',
      title="Test Reg. Req.%s" % new_id,
      reference="TESTREGREQ-%s" % new_id,
      resource='foo/bar',
      )

  def createInstanceTree(self):
    new_id = self.generateNewId()
    instance_tree = self.portal.instance_tree_module\
        .template_instance_tree.Base_createCloneDocument(batch_mode=1)
    instance_tree.edit(
      reference="TESTHS-%s" % new_id,
    )
    instance_tree.validate()
    self.portal.portal_workflow._jumpToStateFor(
        instance_tree, 'start_requested')
    return instance_tree

  def test_deleteInstanceTreeList_REQUEST_disallowed(self):
    ticket = self.createRegularisationRequest()
    self.assertRaises(
      Unauthorized,
      ticket.RegularisationRequest_deleteInstanceTreeList,
      'footag',
      REQUEST={})

  @simulate('InstanceTree_deleteFromRegularisationRequest',
            'person, REQUEST=None',
  'context.portal_workflow.doActionFor(' \
  'context, action="edit_action", ' \
  'comment="Visited by InstanceTree_deleteFromRegularisationRequest ' \
  '%s" % (person))')
  def test_deleteInstanceTreeList_matching_subscription(self):
    person = self.makePerson(index=0, user=0)
    ticket = self.createRegularisationRequest()
    instance_tree = self.createInstanceTree()

    ticket.edit(
      source_project_value=person,
      resource='service_module/slapos_crm_delete_acknowledgement',
    )
    ticket.validate()
    ticket.suspend()
    instance_tree.edit(
      destination_section=person.getRelativeUrl(),
    )
    self.tic()

    result = ticket.\
        RegularisationRequest_deleteInstanceTreeList('footag')
    self.assertTrue(result)

    self.tic()
    self.assertEqual(
      'Visited by InstanceTree_deleteFromRegularisationRequest ' \
      '%s' % person.getRelativeUrl(),
      instance_tree.workflow_history['edit_workflow'][-1]['comment'])

  @simulate('InstanceTree_deleteFromRegularisationRequest',
            '*args, **kwargs',
            'raise NotImplementedError, "Should not have been called"')
  def test_deleteInstanceTreeList_other_subscription(self):
    person = self.makePerson(index=0, user=0)
    ticket = self.createRegularisationRequest()
    self.createInstanceTree()

    ticket.edit(
      source_project_value=person,
      resource='service_module/slapos_crm_delete_acknowledgement',
    )
    ticket.validate()
    ticket.suspend()

    self.tic()

    result = ticket.\
        RegularisationRequest_deleteInstanceTreeList('footag')
    self.assertTrue(result)

    self.tic()

  @simulate('InstanceTree_deleteFromRegularisationRequest',
            '*args, **kwargs',
            'raise NotImplementedError, "Should not have been called"')
  def test_deleteInstanceTreeList_no_person(self):
    ticket = self.createRegularisationRequest()

    ticket.edit(
      resource='service_module/slapos_crm_delete_acknowledgement',
    )
    ticket.validate()
    ticket.suspend()

    self.tic()

    result = ticket.\
        RegularisationRequest_deleteInstanceTreeList('footag')
    self.assertFalse(result)

    self.tic()

  @simulate('InstanceTree_deleteFromRegularisationRequest',
            '*args, **kwargs',
            'raise NotImplementedError, "Should not have been called"')
  def test_deleteInstanceTreeList_not_suspended(self):
    person = self.makePerson(index=0, user=0)
    ticket = self.createRegularisationRequest()
    self.createInstanceTree()

    ticket.edit(
      source_project_value=person,
      resource='service_module/slapos_crm_delete_acknowledgement',
    )
    ticket.validate()

    self.tic()

    result = ticket.\
        RegularisationRequest_deleteInstanceTreeList('footag')
    self.assertFalse(result)

    self.tic()

  @simulate('InstanceTree_deleteFromRegularisationRequest',
            '*args, **kwargs',
            'raise NotImplementedError, "Should not have been called"')
  def test_deleteInstanceTreeList_other_resource(self):
    person = self.makePerson(index=0, user=0)
    ticket = self.createRegularisationRequest()
    self.createInstanceTree()

    ticket.edit(
      source_project_value=person,
      resource='service_module/slapos_crm_delete_reminder',
    )
    ticket.validate()
    ticket.suspend()

    self.tic()

    result = ticket.\
        RegularisationRequest_deleteInstanceTreeList('footag')
    self.assertFalse(result)

    self.tic()
