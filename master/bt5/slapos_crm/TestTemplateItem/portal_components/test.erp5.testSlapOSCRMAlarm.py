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
  SlapOSTestCaseMixin, SlapOSTestCaseMixinWithAbort, simulate, TemporaryAlarmScript
from DateTime import DateTime
import time
import difflib
import transaction
from zExceptions import Unauthorized


class TestSlapOSCRMCreateRegularisationRequestAlarm(SlapOSTestCaseMixin):
  def createFinalInvoice(self, person, grouping_reference=None,
                         ledger="automated",
                         source="account_module/receivable",
                         is_stopped=True):

    current_invoice = self.portal.accounting_module.newContent(
      portal_type="Sale Invoice Transaction",
        destination_section_value=person,
        start_date=DateTime('2019/10/20'),
        stop_date=DateTime('2019/10/20'),
        title='Fake Invoice for Demo User Functional',
        resource="currency_module/EUR",
        reference='1',
        ledger=ledger)
    current_invoice.receivable.edit(
      source=source,
      quantity=1,
      price=1,
      grouping_reference=grouping_reference
    )
    current_invoice.plan()
    current_invoice.confirm()
    if is_stopped:
      current_invoice.stop()

    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm', "'disabled'", attribute='comment'):
      self.tic()
    return current_invoice

  #################################################################
  # slapos_crm_create_regularisation_request
  #################################################################
  def test_Person_checkToCreateRegularisationRequest_alarm_expectedPerson(self):
    new_id = self.generateNewId()
    person = self.portal.person_module.newContent(
      portal_type='Person',
      title="Test person %s" % new_id
      )
    person.validate()
    self.createFinalInvoice(person)
    self.tic()
    self._test_alarm(
      self.portal.portal_alarms.slapos_crm_create_regularisation_request,
      person,
      'Person_checkToCreateRegularisationRequest'
    )

  def test_Person_checkToCreateRegularisationRequest_alarm_started(self):
    new_id = self.generateNewId()
    person = self.portal.person_module.newContent(
      portal_type='Person',
      title="Test person %s" % new_id
      )
    person.validate()
    self.createFinalInvoice(person, is_stopped=False)
    self.tic()
    self._test_alarm_not_visited(
      self.portal.portal_alarms.slapos_crm_create_regularisation_request,
      person,
      'Person_checkToCreateRegularisationRequest'
    )

  def test_Person_checkToCreateRegularisationRequest_alarm_lettered(self):
    new_id = self.generateNewId()
    person = self.portal.person_module.newContent(
      portal_type='Person',
      title="Test person %s" % new_id
      )
    person.validate()
    self.createFinalInvoice(person, grouping_reference="foobar")
    self.tic()
    self._test_alarm_not_visited(
      self.portal.portal_alarms.slapos_crm_create_regularisation_request,
      person,
      'Person_checkToCreateRegularisationRequest'
    )

  def test_Person_checkToCreateRegularisationRequest_alarm_noLedger(self):
    new_id = self.generateNewId()
    person = self.portal.person_module.newContent(
      portal_type='Person',
      title="Test person %s" % new_id
      )
    person.validate()
    self.createFinalInvoice(person, ledger=None)
    self.tic()
    self._test_alarm_not_visited(
      self.portal.portal_alarms.slapos_crm_create_regularisation_request,
      person,
      'Person_checkToCreateRegularisationRequest'
    )

  def test_Person_checkToCreateRegularisationRequest_alarm_noReceivable(self):
    new_id = self.generateNewId()
    person = self.portal.person_module.newContent(
      portal_type='Person',
      title="Test person %s" % new_id
      )
    person.validate()
    self.createFinalInvoice(person, source="account_module/bank")
    self.tic()
    self._test_alarm_not_visited(
      self.portal.portal_alarms.slapos_crm_create_regularisation_request,
      person,
      'Person_checkToCreateRegularisationRequest'
    )

  def test_Person_checkToCreateRegularisationRequest_alarm_notValidatedPerson(self):
    new_id = self.generateNewId()
    person = self.portal.person_module.newContent(
      portal_type='Person',
      title="Test person %s" % new_id
      )
    person.validate()
    person.invalidate()
    self.createFinalInvoice(person)
    self.tic()
    self._test_alarm_not_visited(
      self.portal.portal_alarms.slapos_crm_create_regularisation_request,
      person,
      'Person_checkToCreateRegularisationRequest'
    )

  def test_Person_checkToCreateRegularisationRequest_alarm_noInvoice(self):
    new_id = self.generateNewId()
    person = self.portal.person_module.newContent(
      portal_type='Person',
      title="Test person %s" % new_id
      )
    person.validate()
    self.tic()
    self._test_alarm_not_visited(
      self.portal.portal_alarms.slapos_crm_create_regularisation_request,
      person,
      'Person_checkToCreateRegularisationRequest'
    )

  @simulate('NotificationTool_getDocumentValue',
            'reference=None, language="en"',
  'assert reference == "slapos-crm.create.regularisation.request"\n' \
  'return')
  @simulate('Entity_hasOutstandingAmount', '*args, **kwargs', 'return True')
  def test_Person_checkToCreateRegularisationRequest_script_paymentRequested(self):
    for preference in \
      self.portal.portal_catalog(portal_type="System Preference"):
      preference = preference.getObject()
      if preference.getPreferenceState() == 'global':
        preference.setPreferredSlaposWebSiteUrl('http://foobar.org/')

    project = self.addProject()
    person = self.makePerson(project, index=0, user=0)

    self.createFinalInvoice(person)
    self.tic()

    before_date = DateTime()
    ticket, event = person.Person_checkToCreateRegularisationRequest()
    after_date = DateTime()

    self.tic()

    self.assertEqual(ticket.getPortalType(), 'Regularisation Request')
    self.assertEqual(ticket.getSimulationState(), 'suspended')
    self.assertEqual(ticket.getResource(),
                      'service_module/slapos_crm_acknowledgement')
    self.assertEqual(ticket.getTitle(),
           'Account regularisation expected for "%s"' % person.getTitle())
    self.assertEqual(ticket.getDestination(),
                      person.getRelativeUrl())
    self.assertEqual(ticket.getDestinationDecision(),
                      person.getRelativeUrl())
    self.assertEqual(event.getPortalType(), 'Mail Message')
    self.assertEqual(event.getFollowUp(), ticket.getRelativeUrl())
    self.assertEqual(event.getResource(),
                      'service_module/slapos_crm_acknowledgement')
    self.assertTrue(event.getStartDate() >= before_date)
    self.assertTrue(event.getStopDate() <= after_date)
    self.assertEqual(event.getTitle(), "Invoice payment requested")
    self.assertEqual(event.getDestination(),
                      person.getRelativeUrl())
    self.assertEqual(event.getSource(),
                      ticket.getSource())
    expected_text_content = """Dear %s,

A new invoice has been generated.
You can access it in your invoice section at http://foobar.org/.

Regards,
The slapos team
""" % person.getTitle()
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
  @simulate('Entity_hasOutstandingAmount', '*args, **kwargs', 'return True')
  def test_Person_checkToCreateRegularisationRequest_script_notificationMessage(self):
    for preference in \
      self.portal.portal_catalog(portal_type="System Preference"):
      preference = preference.getObject()
      if preference.getPreferenceState() == 'global':
        preference.setPreferredSlaposWebSiteUrl('http://foobar.org/')

    project = self.addProject()
    person = self.makePerson(project, index=0, user=0)
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
    self.assertEqual(ticket.getSourceProject(), None)
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

  @simulate('Entity_hasOutstandingAmount', '*args, **kwargs', 'return True')
  def test_Person_checkToCreateRegularisationRequest_script_doNotDuplicateTicketIfNotReindexed(self):
    project = self.addProject()
    person = self.makePerson(project, index=0, user=0)
    ticket, event = person.Person_checkToCreateRegularisationRequest()
    transaction.commit()
    ticket2, event2 = person.Person_checkToCreateRegularisationRequest()
    self.assertNotEqual(ticket, None)
    self.assertNotEqual(event, None)
    self.assertEqual(ticket2, None)
    self.assertEqual(event2, None)

  @simulate('Entity_hasOutstandingAmount', '*args, **kwargs', 'return False')
  @simulate('RegularisationRequest_checkToSendUniqEvent',
            '*args, **kwargs',
            'raise NotImplementedError, "Should not have been called"')
  def test_Person_checkToCreateRegularisationRequest_script_balanceOk(self):
    project = self.addProject()
    person = self.makePerson(project, index=0, user=0)
    ticket, event = person.Person_checkToCreateRegularisationRequest()
    self.assertEqual(ticket, None)
    self.assertEqual(event, None)

  @simulate('Entity_hasOutstandingAmount', '*args, **kwargs', 'return True')
  def test_Person_checkToCreateRegularisationRequest_script_existingSuspendedTicket(self):
    project = self.addProject()
    person = self.makePerson(project, index=0, user=0)
    ticket, event = person.Person_checkToCreateRegularisationRequest()
    transaction.commit()
    self.tic()
    ticket2, event2 = person.Person_checkToCreateRegularisationRequest()
    self.assertNotEqual(ticket, None)
    self.assertNotEqual(event, None)
    self.assertEqual(ticket2.getRelativeUrl(), ticket.getRelativeUrl())
    self.assertEqual(event2, None)

  @simulate('Entity_hasOutstandingAmount', '*args, **kwargs', 'return True')
  def test_Person_checkToCreateRegularisationRequest_script_existingValidatedTicket(self):
    project = self.addProject()
    person = self.makePerson(project, index=0, user=0)
    ticket, event = person.Person_checkToCreateRegularisationRequest()
    ticket.validate()
    transaction.commit()
    self.tic()
    ticket2, event2 = person.Person_checkToCreateRegularisationRequest()
    self.assertNotEqual(ticket, None)
    self.assertNotEqual(event, None)
    self.assertEqual(ticket2.getRelativeUrl(), ticket.getRelativeUrl())
    self.assertEqual(event2, None)

  @simulate('Entity_hasOutstandingAmount', '*args, **kwargs', 'return True')
  def test_Person_checkToCreateRegularisationRequest_script_existingInvalidatedTicket(self):
    project = self.addProject()
    person = self.makePerson(project, index=0, user=0)
    ticket = person.Person_checkToCreateRegularisationRequest()[0]
    ticket.invalidate()
    transaction.commit()
    self.tic()
    ticket2, event2 = person.Person_checkToCreateRegularisationRequest()
    self.assertNotEqual(ticket2.getRelativeUrl(), ticket.getRelativeUrl())
    self.assertNotEqual(event2, None)

  def test_Person_checkToCreateRegularisationRequest_script_REQUEST_disallowed(self):
    project = self.addProject()
    person = self.makePerson(project, index=0, user=0)
    self.assertRaises(
      Unauthorized,
      person.Person_checkToCreateRegularisationRequest,
      REQUEST={})


  def createRegularisationRequest(self):
    new_id = self.generateNewId()
    return self.portal.regularisation_request_module.newContent(
      portal_type='Regularisation Request',
      title="Test Reg. Req.%s" % new_id,
      reference="TESTREGREQ-%s" % new_id,
      )

  #################################################################
  # slapos_crm_invalidate_suspended_regularisation_request
  #################################################################
  def test_RegularisationRequest_invalidateIfPersonBalanceIsOk_alarm_validatedRegularisationRequest(self):
    ticket = self.createRegularisationRequest()
    ticket.validate()
    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_invalidate_suspended_regularisation_request
    self._test_alarm(alarm, ticket, "RegularisationRequest_invalidateIfPersonBalanceIsOk")

  def test_RegularisationRequest_invalidateIfPersonBalanceIsOk_alarm_suspendedRegularisationRequest(self):
    ticket = self.createRegularisationRequest()
    ticket.validate()
    ticket.suspend()
    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_invalidate_suspended_regularisation_request
    self._test_alarm(alarm, ticket, "RegularisationRequest_invalidateIfPersonBalanceIsOk")

  def test_RegularisationRequest_invalidateIfPersonBalanceIsOk_alarm_invalidatedRegularisationRequest(self):
    ticket = self.createRegularisationRequest()
    ticket.validate()
    ticket.invalidate()
    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_invalidate_suspended_regularisation_request
    self._test_alarm_not_visited(alarm, ticket, "RegularisationRequest_invalidateIfPersonBalanceIsOk")

  def test_RegularisationRequest_invalidateIfPersonBalanceIsOk_script_REQUESTdisallowed(self):
    ticket = self.createRegularisationRequest()
    self.assertRaises(
      Unauthorized,
      ticket.RegularisationRequest_invalidateIfPersonBalanceIsOk,
      REQUEST={})

  @simulate('Entity_hasOutstandingAmount', '*args, **kwargs', 'return False')
  def test_RegularisationRequest_invalidateIfPersonBalanceIsOk_script_matchingCase(self):
    project = self.addProject()
    person = self.makePerson(project, index=0, user=0)
    ticket = self.createRegularisationRequest()
    ticket.edit(destination_decision_value=person)
    ticket.validate()
    ticket.suspend()
    ticket.RegularisationRequest_invalidateIfPersonBalanceIsOk()
    self.assertEqual(ticket.getSimulationState(), 'invalidated')

  @simulate('Entity_hasOutstandingAmount', '*args, **kwargs', 'return False')
  def test_RegularisationRequest_invalidateIfPersonBalanceIsOk_script_validated(self):
    project = self.addProject()
    person = self.makePerson(project, index=0, user=0)
    ticket = self.createRegularisationRequest()
    ticket.edit(destination_decision_value=person)
    ticket.validate()
    ticket.RegularisationRequest_invalidateIfPersonBalanceIsOk()
    self.assertEqual(ticket.getSimulationState(), 'invalidated')

  @simulate('Entity_hasOutstandingAmount', '*args, **kwargs', 'return False')
  def test_RegularisationRequest_invalidateIfPersonBalanceIsOk_script_noPerson(self):
    ticket = self.createRegularisationRequest()
    ticket.validate()
    ticket.suspend()
    ticket.RegularisationRequest_invalidateIfPersonBalanceIsOk()
    self.assertEqual(ticket.getSimulationState(), 'suspended')

  @simulate('Entity_hasOutstandingAmount', '*args, **kwargs', 'return True')
  def test_RegularisationRequest_invalidateIfPersonBalanceIsOk_script_wrongBalance(self):
    project = self.addProject()
    person = self.makePerson(project, index=0, user=0)
    ticket = self.createRegularisationRequest()
    ticket.edit(destination_decision_value=person)
    ticket.validate()
    ticket.suspend()
    ticket.RegularisationRequest_invalidateIfPersonBalanceIsOk()
    self.assertEqual(ticket.getSimulationState(), 'suspended')


class TestSlapOSCrmTriggerEscalationOnAcknowledgmentRegularisationRequest(SlapOSTestCaseMixinWithAbort):

  def createRegularisationRequest(self):
    new_id = self.generateNewId()
    return self.portal.regularisation_request_module.newContent(
      portal_type='Regularisation Request',
      title="Test Reg. Req.%s" % new_id,
      reference="TESTREGREQ-%s" % new_id,
      )

  #################################################################
  # slapos_crm_trigger_acknowledgment_escalation
  #################################################################
  def test_RegularisationRequest_triggerAcknowledgmentEscalation_alarm_matchingRegularisationRequest(self):
    ticket = self.createRegularisationRequest()
    ticket.edit(resource='service_module/slapos_crm_acknowledgement')
    ticket.validate()
    ticket.suspend()

    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_trigger_acknowledgment_escalation
    self._test_alarm(alarm, ticket,
      "RegularisationRequest_triggerAcknowledgmentEscalation")

  def test_RegularisationRequest_triggerAcknowledgmentEscalation_alarm_notSuspendedRegularisationRequest(self):
    ticket = self.createRegularisationRequest()
    ticket.edit(resource='service_module/slapos_crm_acknowledgement')
    ticket.validate()

    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_trigger_acknowledgment_escalation
    self._test_alarm_not_visited(alarm, ticket,
      "RegularisationRequest_triggerAcknowledgmentEscalation")


  def test_RegularisationRequest_triggerAcknowledgmentEscalation_alarm_notExpectedResource(self):
    ticket = self.createRegularisationRequest()
    ticket.validate()
    ticket.suspend()

    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_trigger_acknowledgment_escalation
    self._test_alarm_not_visited(alarm, ticket,
      "RegularisationRequest_triggerAcknowledgmentEscalation")

  def test_RegularisationRequest_triggerAcknowledgmentEscalation_script_REQUESTdisallowed(self):
    ticket = self.createRegularisationRequest()
    self.assertRaises(
      Unauthorized,
      ticket.RegularisationRequest_triggerAcknowledgmentEscalation,
      REQUEST={})

  @simulate('RegularisationRequest_checkToTriggerNextEscalationStep',
            'delay_period_in_days, current_service_relative_url, ' \
            'next_service_relative_url, title, text_content, comment, ' \
            'notification_message=None, substitution_method_parameter_dict=None, ' \
            'REQUEST=None',
  'import json\n' \
  'context.portal_workflow.doActionFor(' \
  'context, action="edit_action", ' \
  'comment="Visited by RegularisationRequest_checkToTriggerNextEscalationStep ' \
  '%s %s %s %s %s %s %s %s" % (delay_period_in_days, current_service_relative_url, next_service_relative_url, title, text_content, comment, notification_message, json.dumps(substitution_method_parameter_dict, sort_keys=True)))')
  def test_RegularisationRequest_triggerAcknowledgmentEscalation_script_matchingEvent(self):
    ticket = self.createRegularisationRequest()
    ticket.RegularisationRequest_triggerAcknowledgmentEscalation()
    self.assertEqual(
      'Visited by RegularisationRequest_checkToTriggerNextEscalationStep ' \
      '%s %s %s %s %s %s %s %s' % \
      (15,
       'service_module/slapos_crm_acknowledgement',
       'service_module/slapos_crm_delete_reminder',
       'Reminder: invoice payment requested',
"""Dear user,

We would like to remind you the unpaid invoice you have on %s.
If no payment is done during the coming days, we will stop all your current instances to free some hardware resources.

Regards,
The slapos team
""" % self.portal.portal_preferences.getPreferredSlaposWebSiteUrl(),
       'Stopping reminder.',
       'slapos-crm.acknowledgment.escalation',
       '{"days": 15, "user_name": null}'),
      ticket.workflow_history['edit_workflow'][-1]['comment'])


class TestSlapOSCrmTriggerEscalationOnStopReminderRegularisationRequest(SlapOSTestCaseMixinWithAbort):

  def createRegularisationRequest(self):
    new_id = self.generateNewId()
    return self.portal.regularisation_request_module.newContent(
      portal_type='Regularisation Request',
      title="Test Reg. Req.%s" % new_id,
      reference="TESTREGREQ-%s" % new_id,
      )

  #################################################################
  # slapos_crm_trigger_stop_reminder_escalation
  #################################################################
  def test_RegularisationRequest_triggerStopReminderEscalation_alarm_matchingRegularisationRequest(self):
    ticket = self.createRegularisationRequest()
    ticket.edit(resource='service_module/slapos_crm_stop_reminder')
    ticket.validate()
    ticket.suspend()

    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_trigger_stop_reminder_escalation
    self._test_alarm(alarm, ticket,
      "RegularisationRequest_triggerStopReminderEscalation")

  def test_RegularisationRequest_triggerStopReminderEscalation_alarm_notSuspended(self):
    ticket = self.createRegularisationRequest()
    ticket.edit(resource='service_module/slapos_crm_stop_reminder')
    ticket.validate()

    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_trigger_stop_reminder_escalation
    self._test_alarm_not_visited(alarm, ticket,
      "RegularisationRequest_triggerStopReminderEscalation")

  def test_RegularisationRequest_triggerStopReminderEscalation_alarm_notExpectedResource(self):
    ticket = self.createRegularisationRequest()
    ticket.validate()
    ticket.suspend()

    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_trigger_stop_reminder_escalation
    self._test_alarm_not_visited(alarm, ticket,
      "RegularisationRequest_triggerStopReminderEscalation")

  def test_RegularisationRequest_triggerStopReminderEscalation_script_REQUESTdisallowed(self):
    ticket = self.createRegularisationRequest()
    self.assertRaises(
      Unauthorized,
      ticket.RegularisationRequest_triggerStopReminderEscalation,
      REQUEST={})

  @simulate('RegularisationRequest_checkToTriggerNextEscalationStep',
            'delay_period_in_days, current_service_relative_url, ' \
            'next_service_relative_url, title, text_content, comment, ' \
            'notification_message=None, substitution_method_parameter_dict=None, ' \
            'REQUEST=None',
            'import json\n' \
            'context.portal_workflow.doActionFor(' \
  'context, action="edit_action", ' \
  'comment="Visited by RegularisationRequest_checkToTriggerNextEscalationStep ' \
  '%s %s %s %s %s %s %s %s" % (delay_period_in_days, current_service_relative_url, next_service_relative_url, title, text_content, comment, notification_message, json.dumps(substitution_method_parameter_dict, sort_keys=True)))')
  def test_RegularisationRequest_triggerStopReminderEscalation_script_matchingEvent(self):
    ticket = self.createRegularisationRequest()
    ticket.RegularisationRequest_triggerStopReminderEscalation()
    self.assertEqual(
      'Visited by RegularisationRequest_checkToTriggerNextEscalationStep ' \
      '%s %s %s %s %s %s %s %s' % \
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
       'Stopping acknowledgment.',
       'slapos-crm.stop.reminder.escalation',
       '{"days": 7, "user_name": null}'),
      ticket.workflow_history['edit_workflow'][-1]['comment'])


class TestSlapOSCrmTriggerEscalationOnStopAcknowledgmentRegularisationRequest(SlapOSTestCaseMixinWithAbort):

  def createRegularisationRequest(self):
    new_id = self.generateNewId()
    return self.portal.regularisation_request_module.newContent(
      portal_type='Regularisation Request',
      title="Test Reg. Req.%s" % new_id,
      reference="TESTREGREQ-%s" % new_id,
      )

  #################################################################
  # slapos_crm_trigger_stop_acknowledgment_escalation
  #################################################################
  def test_RegularisationRequest_triggerStopAcknowledgmentEscalation_alarm_matchingRegularisationRequest(self):
    ticket = self.createRegularisationRequest()
    ticket.edit(resource='service_module/slapos_crm_stop_acknowledgement')
    ticket.validate()
    ticket.suspend()

    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_trigger_stop_acknowledgment_escalation
    self._test_alarm(alarm, ticket,
      "RegularisationRequest_triggerStopAcknowledgmentEscalation")

  def test_RegularisationRequest_triggerStopAcknowledgmentEscalation_alarm_notSuspended(self):
    ticket = self.createRegularisationRequest()
    ticket.edit(resource='service_module/slapos_crm_stop_acknowledgement')
    ticket.validate()

    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_trigger_stop_acknowledgment_escalation
    self._test_alarm_not_visited(alarm, ticket,
      "RegularisationRequest_triggerStopAcknowledgmentEscalation")

  def test_RegularisationRequest_triggerStopAcknowledgmentEscalation_alarm_notExpectedResource(self):
    ticket = self.createRegularisationRequest()
    ticket.validate()
    ticket.suspend()

    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_trigger_stop_acknowledgment_escalation
    self._test_alarm_not_visited(alarm, ticket,
      "RegularisationRequest_triggerStopAcknowledgmentEscalation")

  def test_RegularisationRequest_triggerStopAcknowledgmentEscalation_script_REQUESTdisallowed(self):
    ticket = self.createRegularisationRequest()
    self.assertRaises(
      Unauthorized,
      ticket.RegularisationRequest_triggerStopAcknowledgmentEscalation,
      REQUEST={})

  @simulate('RegularisationRequest_checkToTriggerNextEscalationStep',
            'delay_period_in_days, current_service_relative_url, ' \
            'next_service_relative_url, title, text_content, comment, ' \
            'notification_message=None, substitution_method_parameter_dict=None, ' \
            'REQUEST=None',
            'import json\n' \
            'context.portal_workflow.doActionFor(' \
  'context, action="edit_action", ' \
  'comment="Visited by RegularisationRequest_checkToTriggerNextEscalationStep ' \
  '%s %s %s %s %s %s %s %s" % (delay_period_in_days, current_service_relative_url, next_service_relative_url, title, text_content, comment, notification_message, json.dumps(substitution_method_parameter_dict, sort_keys=True)))')
  def test_RegularisationRequest_triggerStopAcknowledgmentEscalation_script_matchingEvent(self):
    ticket = self.createRegularisationRequest()
    ticket.RegularisationRequest_triggerStopAcknowledgmentEscalation()
    self.assertEqual(
      'Visited by RegularisationRequest_checkToTriggerNextEscalationStep ' \
      '%s %s %s %s %s %s %s %s' % \
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
       'Deleting reminder.',
       'slapos-crm.stop.acknowledgment.escalation',
       '{"days": 7, "user_name": null}'),
      ticket.workflow_history['edit_workflow'][-1]['comment'])


class TestSlapOSCrmTriggerEscalationOnDeleteReminderRegularisationRequest(SlapOSTestCaseMixinWithAbort):

  def createRegularisationRequest(self):
    new_id = self.generateNewId()
    return self.portal.regularisation_request_module.newContent(
      portal_type='Regularisation Request',
      title="Test Reg. Req.%s" % new_id,
      reference="TESTREGREQ-%s" % new_id,
      )

  #################################################################
  # slapos_crm_trigger_delete_reminder_escalation
  #################################################################
  def test_RegularisationRequest_triggerDeleteReminderEscalation_alarm_matchingRegularisationRequest(self):
    ticket = self.createRegularisationRequest()
    ticket.edit(resource='service_module/slapos_crm_delete_reminder')
    ticket.validate()
    ticket.suspend()

    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_trigger_delete_reminder_escalation
    self._test_alarm(alarm, ticket, "RegularisationRequest_triggerDeleteReminderEscalation")

  def test_RegularisationRequest_triggerDeleteReminderEscalation_alarm_notSuspended(self):
    ticket = self.createRegularisationRequest()
    ticket.edit(resource='service_module/slapos_crm_delete_reminder')
    ticket.validate()

    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_trigger_delete_reminder_escalation
    self._test_alarm_not_visited(alarm, ticket, "RegularisationRequest_triggerDeleteReminderEscalation")

  def test_RegularisationRequest_triggerDeleteReminderEscalation_alarm_notExpectedResource(self):
    ticket = self.createRegularisationRequest()
    ticket.validate()
    ticket.suspend()

    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_trigger_delete_reminder_escalation
    self._test_alarm_not_visited(alarm, ticket, "RegularisationRequest_triggerDeleteReminderEscalation")

  def test_RegularisationRequest_triggerDeleteReminderEscalation_script_REQUESTdisallowed(self):
    ticket = self.createRegularisationRequest()
    self.assertRaises(
      Unauthorized,
      ticket.RegularisationRequest_triggerDeleteReminderEscalation,
      REQUEST={})

  @simulate('RegularisationRequest_checkToTriggerNextEscalationStep',
            'delay_period_in_days, current_service_relative_url, ' \
            'next_service_relative_url, title, text_content, comment, ' \
            'notification_message=None, substitution_method_parameter_dict=None, ' \
            'REQUEST=None',
            'import json\n' \
            'context.portal_workflow.doActionFor(' \
  'context, action="edit_action", ' \
  'comment="Visited by RegularisationRequest_checkToTriggerNextEscalationStep ' \
  '%s %s %s %s %s %s %s %s" % (delay_period_in_days, current_service_relative_url, next_service_relative_url, title, text_content, comment, notification_message, json.dumps(substitution_method_parameter_dict, sort_keys=True)))')
  def test_RegularisationRequest_triggerDeleteReminderEscalation_script_matchingEvent(self):
    ticket = self.createRegularisationRequest()
    ticket.RegularisationRequest_triggerDeleteReminderEscalation()
    self.assertEqual(
      'Visited by RegularisationRequest_checkToTriggerNextEscalationStep ' \
      '%s %s %s %s %s %s %s %s' % \
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
       'Deleting acknowledgment.',
       'slapos-crm.delete.reminder.escalation',
       '{"days": 10, "user_name": null}'),
      ticket.workflow_history['edit_workflow'][-1]['comment'])


class TestSlapOSCrmStopInstanceTree(SlapOSTestCaseMixinWithAbort):

  def createRegularisationRequest(self):
    new_id = self.generateNewId()
    return self.portal.regularisation_request_module.newContent(
      portal_type='Regularisation Request',
      title="Test Reg. Req.%s" % new_id,
      reference="TESTREGREQ-%s" % new_id,
      )

  #################################################################
  # slapos_crm_trigger_delete_reminder_escalation
  #################################################################
  def test_RegularisationRequest_stopInstanceTreeList_alarm_matchingRegularisationRequest(self):
    ticket = self.createRegularisationRequest()
    ticket.edit(resource='service_module/slapos_crm_delete_reminder')
    ticket.validate()
    ticket.suspend()

    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_stop_instance_tree
    self._test_alarm(alarm, ticket, "RegularisationRequest_stopInstanceTreeList")

  def test_RegularisationRequest_stopInstanceTreeList_alarm_matchingRegularisationRequest2(self):
    ticket = self.createRegularisationRequest()
    ticket.edit(resource='service_module/slapos_crm_stop_acknowledgement')
    ticket.validate()
    ticket.suspend()

    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_stop_instance_tree
    self._test_alarm(alarm, ticket, "RegularisationRequest_stopInstanceTreeList")

  def test_RegularisationRequest_stopInstanceTreeList_alarm_notSuspended(self):
    ticket = self.createRegularisationRequest()
    ticket.edit(resource='service_module/slapos_crm_stop_acknowledgement')
    ticket.validate()

    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_stop_instance_tree
    self._test_alarm_not_visited(alarm, ticket, "RegularisationRequest_stopInstanceTreeList")

  def test_RegularisationRequest_stopInstanceTreeList_alarm_otherResource(self):
    ticket = self.createRegularisationRequest()
    ticket.edit(resource='service_module/slapos_acknowledgement')
    ticket.validate()
    ticket.suspend()

    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_stop_instance_tree
    self._test_alarm_not_visited(alarm, ticket, "RegularisationRequest_stopInstanceTreeList")

  def createInstanceTree(self):
    new_id = self.generateNewId()
    instance_tree = self.portal.instance_tree_module\
        .newContent(portal_type="Instance Tree")
    instance_tree.edit(
      reference="TESTHS-%s" % new_id,
    )
    instance_tree.validate()
    self.portal.portal_workflow._jumpToStateFor(
        instance_tree, 'start_requested')
    return instance_tree

  def test_RegularisationRequest_stopInstanceTreeList_script_REQUESTdisallowed(self):
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
  def test_RegularisationRequest_stopInstanceTreeList_script_matchingSubscription(self):
    project = self.addProject()
    person = self.makePerson(project, index=0, user=0)
    ticket = self.createRegularisationRequest()
    instance_tree = self.createInstanceTree()

    ticket.edit(
      destination_decision_value=person,
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
  def test_RegularisationRequest_stopInstanceTreeList_script_matchingSubscription2(self):
    project = self.addProject()
    person = self.makePerson(project, index=0, user=0)
    ticket = self.createRegularisationRequest()
    instance_tree = self.createInstanceTree()

    ticket.edit(
      destination_decision_value=person,
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
  def test_RegularisationRequest_stopInstanceTreeList_script_otherSubscription(self):
    project = self.addProject()
    person = self.makePerson(project, index=0, user=0)
    ticket = self.createRegularisationRequest()
    self.createInstanceTree()

    ticket.edit(
      destination_decision_value=person,
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
  def test_RegularisationRequest_stopInstanceTreeList_script_noPerson(self):
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
  def test_RegularisationRequest_stopInstanceTreeList_script_notSuspended(self):
    project = self.addProject()
    person = self.makePerson(project, index=0, user=0)
    ticket = self.createRegularisationRequest()
    self.createInstanceTree()

    ticket.edit(
      destination_decision_value=person,
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
  def test_RegularisationRequest_stopInstanceTreeList_script_otherResource(self):
    project = self.addProject()
    person = self.makePerson(project, index=0, user=0)
    ticket = self.createRegularisationRequest()
    self.createInstanceTree()

    ticket.edit(
      destination_decision_value=person,
      resource='service_module/slapos_crm_acknowledgement',
    )
    ticket.validate()
    ticket.suspend()

    self.tic()

    result = ticket.\
        RegularisationRequest_stopInstanceTreeList('footag')
    self.assertFalse(result)

    self.tic()


class TestSlapOSCrmDeleteInstanceTree(SlapOSTestCaseMixinWithAbort):
  launch_caucase = 1

  def createRegularisationRequest(self):
    new_id = self.generateNewId()
    return self.portal.regularisation_request_module.newContent(
      portal_type='Regularisation Request',
      title="Test Reg. Req.%s" % new_id,
      reference="TESTREGREQ-%s" % new_id,
      resource='foo/bar',
      )

  #################################################################
  # slapos_crm_delete_instance_tree
  #################################################################
  def test_RegularisationRequest_deleteInstanceTreeList_alarm_matchingRegularisationRequest(self):
    ticket = self.createRegularisationRequest()
    ticket.edit(resource='service_module/slapos_crm_delete_acknowledgement')
    ticket.validate()
    ticket.suspend()

    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_delete_instance_tree
    self._test_alarm(alarm, ticket, "RegularisationRequest_deleteInstanceTreeList")

  def test_RegularisationRequest_deleteInstanceTreeList_alarm_notSuspended(self):
    ticket = self.createRegularisationRequest()
    ticket.edit(resource='service_module/slapos_crm_delete_acknowledgement')
    ticket.validate()

    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_delete_instance_tree
    self._test_alarm_not_visited(alarm, ticket, "RegularisationRequest_deleteInstanceTreeList")

  def test_RegularisationRequest_deleteInstanceTreeList_alarm_otherResource(self):
    ticket = self.createRegularisationRequest()
    ticket.edit(resource='service_module/slapos_crm_delete_reminder')
    ticket.validate()
    ticket.suspend()

    self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_delete_instance_tree
    self._test_alarm_not_visited(alarm, ticket, "RegularisationRequest_deleteInstanceTreeList")

  def createInstanceTree(self):
    new_id = self.generateNewId()
    instance_tree = self.portal.instance_tree_module\
        .newContent(portal_type="Instance Tree")
    instance_tree.edit(
      reference="TESTHS-%s" % new_id,
    )
    instance_tree.validate()
    self.portal.portal_workflow._jumpToStateFor(
        instance_tree, 'start_requested')
    return instance_tree

  def test_RegularisationRequest_deleteInstanceTreeList_script_REQUESTdisallowed(self):
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
  def test_RegularisationRequest_deleteInstanceTreeList_script_matchingSubscription(self):
    _, _, _, _, _, instance_tree = \
      self.bootstrapAllocableInstanceTree(is_accountable=True, base_price=3, )
    person = instance_tree.getDestinationSectionValue()
    ticket = self.createRegularisationRequest()

    ticket.edit(
      destination_decision_value=person,
      resource='service_module/slapos_crm_delete_acknowledgement',
    )
    ticket.validate()
    ticket.suspend()

    accounting_transaction = self.portal.accounting_module.newContent(
      portal_type="Sale Invoice Transaction",
      destination_section_value=person,
      start_date=DateTime(),
      price_currency="currency_module/EUR",
      resource="currency_module/EUR",
      ledger="automated",
    )
    accounting_transaction.newContent(
      portal_type="Invoice Line",
      aggregate_value_list=[
        instance_tree,
        self.portal.hosting_subscription_module.newContent()
      ]
    )
    accounting_transaction.newContent(
      portal_type="Sale Invoice Transaction Line",
      quantity=1,
      source="account_module/receivable"
    )
    self.portal.portal_workflow._jumpToStateFor(accounting_transaction, 'stopped')
    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm', "'disabled'", attribute='comment'):
      self.tic()

    result = ticket.\
        RegularisationRequest_deleteInstanceTreeList('footag')
    self.assertTrue(result)

    self.tic()
    self.assertEqual(
      'Visited by InstanceTree_deleteFromRegularisationRequest ' \
      '%s' % person.getRelativeUrl(),
      instance_tree.workflow_history['edit_workflow'][-1]['comment'])

    # The test impacts all others
    # workaround by deleting the object
    accounting_transaction.getParentValue().manage_delObjects([accounting_transaction.getId()])
    ticket.getParentValue().manage_delObjects([ticket.getId()])
    self.tic()

  @simulate('InstanceTree_deleteFromRegularisationRequest',
            '*args, **kwargs',
            'raise NotImplementedError, "Should not have been called"')
  def test_RegularisationRequest_deleteInstanceTreeList_script_otherSubscription(self):
    project = self.addProject()
    person = self.makePerson(project, index=0, user=0)
    ticket = self.createRegularisationRequest()
    self.createInstanceTree()

    ticket.edit(
      destination_decision_value=person,
      resource='service_module/slapos_crm_delete_acknowledgement',
    )
    ticket.validate()
    ticket.suspend()

    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm', "'disabled'", attribute='comment'):
      self.tic()

    result = ticket.\
        RegularisationRequest_deleteInstanceTreeList('footag')
    self.assertTrue(result)

    self.tic()

  @simulate('InstanceTree_deleteFromRegularisationRequest',
            '*args, **kwargs',
            'raise NotImplementedError, "Should not have been called"')
  def test_RegularisationRequest_deleteInstanceTreeList_script_noPerson(self):
    ticket = self.createRegularisationRequest()

    ticket.edit(
      resource='service_module/slapos_crm_delete_acknowledgement',
    )
    ticket.validate()
    ticket.suspend()

    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm', "'disabled'", attribute='comment'):
      self.tic()

    result = ticket.\
        RegularisationRequest_deleteInstanceTreeList('footag')
    self.assertFalse(result)

    self.tic()

  @simulate('InstanceTree_deleteFromRegularisationRequest',
            '*args, **kwargs',
            'raise NotImplementedError, "Should not have been called"')
  def test_RegularisationRequest_deleteInstanceTreeList_script_notSuspended(self):
    project = self.addProject()
    person = self.makePerson(project, index=0, user=0)
    ticket = self.createRegularisationRequest()
    self.createInstanceTree()

    ticket.edit(
      destination_decision_value=person,
      resource='service_module/slapos_crm_delete_acknowledgement',
    )
    ticket.validate()

    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm', "'disabled'", attribute='comment'):
      self.tic()

    result = ticket.\
        RegularisationRequest_deleteInstanceTreeList('footag')
    self.assertFalse(result)

    self.tic()

  @simulate('InstanceTree_deleteFromRegularisationRequest',
            '*args, **kwargs',
            'raise NotImplementedError, "Should not have been called"')
  def test_RegularisationRequest_deleteInstanceTreeList_script_otherResource(self):
    project = self.addProject()
    person = self.makePerson(project, index=0, user=0)
    ticket = self.createRegularisationRequest()
    self.createInstanceTree()

    ticket.edit(
      destination_decision_value=person,
      resource='service_module/slapos_crm_delete_reminder',
    )
    ticket.validate()
    ticket.suspend()

    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm', "'disabled'", attribute='comment'):
      self.tic()

    result = ticket.\
        RegularisationRequest_deleteInstanceTreeList('footag')
    self.assertFalse(result)

    self.tic()


class TestSlaposCrmCheckStoppedEventFromRegularisationRequestToDeliver(SlapOSTestCaseMixinWithAbort):

  ticket_portal_type = 'Regularisation Request'
  event_portal_type = 'Web Message'

  def _makeTicket(self):
    ticket = self.portal.getDefaultModule(self.ticket_portal_type).newContent(
      portal_type=self.ticket_portal_type
    )
    ticket.submit()
    new_id = self.generateNewId()
    ticket.edit(
        title= "%s éçà %s" % (self.ticket_portal_type, new_id), #pylint: disable=invalid-encoded-data
        reference="TESTTCK-%s" % new_id
    )
    return ticket

  def _makeEvent(self, ticket):
    new_id = self.generateNewId()
    return self.portal.event_module.newContent(
      portal_type=self.event_portal_type,
      title='Test %s %s' % (self.event_portal_type, new_id),
      follow_up_value=ticket
    )

  def test_Event_checkStoppedEventFromRegularisationRequestToDeliver_alarm_stopped(self):
    ticket = self._makeTicket()
    event = self._makeEvent(ticket)
    event.stop()
    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm', "'disabled'", attribute='comment'):
      self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_check_stopped_event_from_regularisation_request_to_deliver
    self._test_alarm(alarm, event, "Event_checkStoppedFromRegularisationRequestToDeliver")

  def test_Event_checkStoppedEventFromRegularisationRequestToDeliver_alarm_delivered(self):
    ticket = self._makeTicket()
    event = self._makeEvent(ticket)
    event.stop()
    event.deliver()
    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm', "'disabled'", attribute='comment'):
      self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_check_stopped_event_from_regularisation_request_to_deliver
    self._test_alarm_not_visited(alarm, event, "Event_checkStoppedFromRegularisationRequestToDeliver")

  def test_Event_checkStoppedEventFromRegularisationRequestToDeliver_alarm_stoppedWithoutTicket(self):
    ticket = self._makeTicket()
    event = self._makeEvent(ticket)
    event.setFollowUp(None)
    event.stop()
    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm', "'disabled'", attribute='comment'):
      self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_crm_check_stopped_event_from_regularisation_request_to_deliver
    self._test_alarm_not_visited(alarm, event, "Event_checkStoppedFromRegularisationRequestToDeliver")

  def test_Event_checkStoppedEventFromRegularisationRequestToDeliver_script_recentEventInvalidatedTicket(self):
    ticket = self._makeTicket()
    ticket.validate()
    ticket.invalidate()
    self.tic()
    time.sleep(1)
    event = self._makeEvent(ticket)
    event.stop()
    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm', "'disabled'", attribute='comment'):
      self.tic()
    self.assertEqual(event.getSimulationState(), "stopped")
    self.assertEqual(ticket.getSimulationState(), "invalidated")
    event.Event_checkStoppedFromRegularisationRequestToDeliver()
    self.assertEqual(event.getSimulationState(), "delivered")
    self.assertEqual(ticket.getSimulationState(), "invalidated")

  def test_Event_checkStoppedEventFromRegularisationRequestToDeliver_script_recentEventValidatedTicket(self):
    ticket = self._makeTicket()
    ticket.validate()
    self.tic()
    time.sleep(1)
    event = self._makeEvent(ticket)
    event.stop()
    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm', "'disabled'", attribute='comment'):
      self.tic()
    self.assertEqual(event.getSimulationState(), "stopped")
    self.assertEqual(ticket.getSimulationState(), "validated")
    event.Event_checkStoppedFromRegularisationRequestToDeliver()
    self.assertEqual(event.getSimulationState(), "delivered")
    self.assertTrue(event.getCreationDate() < ticket.getModificationDate())
    self.assertEqual(ticket.getSimulationState(), "validated")

  def test_Event_checkStoppedEventFromRegularisationRequestToDeliver_script_recentEventSuspendedTicket(self):
    ticket = self._makeTicket()
    ticket.validate()
    ticket.suspend()
    self.tic()
    time.sleep(1)
    event = self._makeEvent(ticket)
    event.stop()
    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm', "'disabled'", attribute='comment'):
      self.tic()
    self.assertEqual(event.getSimulationState(), "stopped")
    self.assertEqual(ticket.getSimulationState(), "suspended")
    event.Event_checkStoppedFromRegularisationRequestToDeliver()
    self.assertEqual(event.getSimulationState(), "stopped")
    self.assertEqual(ticket.getSimulationState(), "suspended")

  def test_Event_checkStoppedEventFromRegularisationRequestToDeliver_script_oldEventInvalidatedTicket(self):
    ticket = self._makeTicket()
    event = self._makeEvent(ticket)
    event.stop()
    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm', "'disabled'", attribute='comment'):
      self.tic()
    time.sleep(1)
    ticket.validate()
    ticket.invalidate()
    self.tic()
    self.assertEqual(event.getSimulationState(), "stopped")
    self.assertEqual(ticket.getSimulationState(), "invalidated")
    event.Event_checkStoppedFromRegularisationRequestToDeliver()
    self.assertEqual(event.getSimulationState(), "delivered")
    self.assertEqual(ticket.getSimulationState(), "invalidated")

  def test_Event_checkStoppedEventFromRegularisationRequestToDeliver_script_oldEventValidatedTicket(self):
    ticket = self._makeTicket()
    event = self._makeEvent(ticket)
    event.stop()
    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm', "'disabled'", attribute='comment'):
      self.tic()
    time.sleep(1)
    ticket.validate()
    self.tic()
    self.assertEqual(event.getSimulationState(), "stopped")
    self.assertEqual(ticket.getSimulationState(), "validated")
    event.Event_checkStoppedFromRegularisationRequestToDeliver()
    self.assertEqual(event.getSimulationState(), "delivered")
    self.assertEqual(ticket.getSimulationState(), "validated")

  def test_Event_checkStoppedEventFromRegularisationRequestToDeliver_script_oldEventSuspendedTicket(self):
    ticket = self._makeTicket()
    event = self._makeEvent(ticket)
    event.stop()
    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm', "'disabled'", attribute='comment'):
      self.tic()
    time.sleep(1)
    ticket.validate()
    ticket.suspend()
    self.tic()
    self.assertEqual(event.getSimulationState(), "stopped")
    self.assertEqual(ticket.getSimulationState(), "suspended")
    event.Event_checkStoppedFromRegularisationRequestToDeliver()
    self.assertEqual(event.getSimulationState(), "stopped")
    self.assertEqual(ticket.getSimulationState(), "suspended")
