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


class TestSlapOSRegularisationRequest_checkToSendUniqEvent(SlapOSTestCaseMixin):
  def afterSetUp(self):
    SlapOSTestCaseMixin.afterSetUp(self)
    expected_slapos_organisation = self.portal.organisation_module.newContent(
      default_email_coordinate_text="foo@example.org"
    )
    self.expected_slapos_organisation = expected_slapos_organisation.getRelativeUrl()

  def createRegularisationRequest(self):
    new_id = self.generateNewId()
    return self.portal.regularisation_request_module.newContent(
      portal_type='Regularisation Request',
      title="Test Reg. Req.%s" % new_id,
      reference="TESTREGREQ-%s" % new_id,
      resource='foo/bar',
      )

  def test_checkToSendUniqEvent_noEvent(self):
    project = self.addProject()
    person = self.makePerson(project, index=0, user=0)
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
    self.assertEqual(event.getContentType(), 'text/plain')

  def test_checkToSendUniqEvent_notificationMessage(self):
    project = self.addProject()
    person = self.makePerson(project, index=0, user=0)
    ticket = self.createRegularisationRequest()
    ticket.edit(
      source=self.expected_slapos_organisation,
      destination_value=person,
      source_project_value=person)
    ticket.validate()
    ticket.suspend()
    before_date = DateTime()

    notification_message_reference = 'test_checkToSendUniqEvent_notificationMessage%s' % self.generateNewId()
    notification_message = self.portal.notification_message_module.newContent(
      portal_type="Notification Message",
      reference=notification_message_reference,
      title='notification title ${foo}',
      text_content_substitution_mapping_method_id='NotificationMessage_getSubstitutionMappingDictFromEvent',
      text_content='notification content ${foo}',
      content_type='text/html',
      )
    notification_message.validate()
    self.tic()

    event = ticket.RegularisationRequest_checkToSendUniqEvent(
      'service_module/slapos_crm_spam', 'foo title', 'foo content',
      'foo comment',
      notification_message=notification_message_reference,
      substitution_method_parameter_dict={'foo': 'bar'}
    )
    after_date = DateTime()

    self.assertEqual(ticket.getSimulationState(), 'suspended')
    self.assertEqual(ticket.getResource(), 'service_module/slapos_crm_spam')

    self.assertEqual(event.getPortalType(), 'Mail Message')
    self.assertEqual(event.getSimulationState(), 'delivered')
    self.assertTrue(event.getStartDate() >= before_date)
    self.assertTrue(event.getStopDate() <= after_date)
    self.assertEqual(event.getTitle(), "notification title bar")
    self.assertEqual(event.getResource(), 'service_module/slapos_crm_spam')
    self.assertEqual(event.getFollowUp(), ticket.getRelativeUrl())
    self.assertEqual(event.getSource(), self.expected_slapos_organisation)
    self.assertEqual(event.getDestination(), person.getRelativeUrl())
    self.assertEqual(event.getTextContent(), 'notification content bar')
    self.assertEqual(event.getContentType(), 'text/html')

  def test_checkToSendUniqEvent_serviceRequired(self):
    ticket = self.createRegularisationRequest()
    self.assertRaises(
      AssertionError,
      ticket.RegularisationRequest_checkToSendUniqEvent,
      ticket.getRelativeUrl(), '', '', ''
      )

  def test_checkToSendUniqEvent_callTwiceWithTic(self):
    project = self.addProject()
    person = self.makePerson(project, index=0, user=0)
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

  def test_checkToSendUniqEvent_manualEvent(self):
    project = self.addProject()
    person = self.makePerson(project, index=0, user=0)
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

  def test_checkToSendUniqEvent_notSuspended(self):
    project = self.addProject()
    person = self.makePerson(project, index=0, user=0)
    ticket = self.createRegularisationRequest()
    ticket.edit(
      source=self.expected_slapos_organisation,
      destination_value=person,
      source_project_value=person)
    ticket.validate()

    event = ticket.RegularisationRequest_checkToSendUniqEvent(
      'service_module/slapos_crm_spam', 'foo2 title', 'foo2 content', 'foo2 comment')
    self.assertEqual(event, None)

  def test_checkToSendUniqEvent_eventNotReindexed(self):
    project = self.addProject()
    person = self.makePerson(project, index=0, user=0)
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

  def test_checkToSendUniqEvent_REQUESTdisallowed(self):
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

  @simulate('RegularisationRequest_checkToSendUniqEvent',
            'service_relative_url, title, text_content, comment, ' \
            'notification_message=None, substitution_method_parameter_dict=None, ' \
            'REQUEST=None',
  'context.portal_workflow.doActionFor(' \
  'context, action="edit_action", ' \
  'comment="Visited by RegularisationRequest_checkToSendUniqEvent ' \
  '%s %s %s %s %s %s" % (service_relative_url, title, text_content, comment, notification_message, substitution_method_parameter_dict))\n' \
  'return "fooevent"')
  def test_checkToTriggerNextEscalationStep_matchingEvent(self):
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
        'foo2 title', 'foo2 content', 'foo2 comment',
        notification_message='slapos-crm.acknowledgment.escalation',
        substitution_method_parameter_dict={'foo': 'bar'})

    self.assertEqual(event2, event.getRelativeUrl())
    self.assertEqual(
      'Visited by RegularisationRequest_checkToSendUniqEvent %s %s %s %s %s %s' % \
      ('service_module/slapos_crm_spam', 'foo2 title', 'foo2 content',
       'foo2 comment', 'slapos-crm.acknowledgment.escalation', {'foo': 'bar'}),
      ticket.workflow_history['edit_workflow'][-1]['comment'])

  @simulate('RegularisationRequest_checkToSendUniqEvent',
            '*args, **kwargs',
            'raise NotImplementedError, "Should not have been called"')
  def test_checkToTriggerNextEscalationStep_recentEvent(self):
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
  def test_checkToTriggerNextEscalationStep_other_ticketEvent(self):
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
  def test_checkToTriggerNextEscalationStep_otherResourceEvent(self):
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
  def test_checkToTriggerNextEscalationStep_noCurrentEvent(self):
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
  def test_checkToTriggerNextEscalationStep_noTicketResource(self):
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
  def test_checkToTriggerNextEscalationStep_notSuspended(self):
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

  def test_checkToTriggerNextEscalationStep_REQUESTdisallowed(self):
    ticket = self.createRegularisationRequest()
    self.assertRaises(
      Unauthorized,
      ticket.RegularisationRequest_checkToTriggerNextEscalationStep,
      '', '', '', '', '', '',
      REQUEST={})


class TestSlapOSInstanceTree_stopFromRegularisationRequest(
                                                          SlapOSTestCaseMixinWithAbort):

  def createInstanceTree(self, project):
    new_id = self.generateNewId()
    instance_tree = self.portal.instance_tree_module\
        .newContent(portal_type="Instance Tree")
    instance_tree.edit(
      reference="TESTHS-%s" % new_id,
      follow_up_value=project,
      url_string=self.generateNewSoftwareReleaseUrl(),
      title=self.generateNewSoftwareTitle(),
      source_reference=self.generateNewSoftwareType(),
      text_content=self.generateSafeXml(),
      sla_xml=self.generateSafeXml(),
      root_slave=False
    )
    instance_tree.validate()
    self.portal.portal_workflow._jumpToStateFor(
        instance_tree, 'start_requested')
    return instance_tree

  def test_stopFromRegularisationRequest_REQUESTdisallowed(self):
    self.assertRaises(
      Unauthorized,
      self.portal.InstanceTree_stopFromRegularisationRequest,
      '',
      REQUEST={})

  def test_stopFromRegularisationRequest_matchingSubscription(self):
    project = self.addProject()
    person = self.makePerson(project, index=0, user=0)
    instance_tree = self.createInstanceTree(project)
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

  def test_stopFromRegularisationRequest_stoppedSubscription(self):
    project = self.addProject()
    person = self.makePerson(project, index=0, user=0)
    instance_tree = self.createInstanceTree(project)
    instance_tree.edit(
      destination_section=person.getRelativeUrl(),
    )
    self.portal.portal_workflow._jumpToStateFor(
        instance_tree, 'stop_requested')

    result = instance_tree.\
        InstanceTree_stopFromRegularisationRequest(person.getRelativeUrl())

    self.assertEqual(result, False)

  def test_stopFromRegularisationRequest_nonMatchingPerson(self):
    project = self.addProject()
    instance_tree = self.createInstanceTree(project)
    self.assertRaises(
      AssertionError,
      instance_tree.InstanceTree_stopFromRegularisationRequest,
      'foobar')


class TestSlapOSInstanceTree_deleteFromRegularisationRequest(
                                                          SlapOSTestCaseMixinWithAbort):

  def createInstanceTree(self, project):
    new_id = self.generateNewId()
    instance_tree = self.portal.instance_tree_module\
        .newContent(portal_type="Instance Tree")
    instance_tree.edit(
      reference="TESTHS-%s" % new_id,
      follow_up_value=project,
      url_string=self.generateNewSoftwareReleaseUrl(),
      title=self.generateNewSoftwareTitle(),
      source_reference=self.generateNewSoftwareType(),
      text_content=self.generateSafeXml(),
      sla_xml=self.generateSafeXml(),
      root_slave=False
    )
    instance_tree.validate()
    self.portal.portal_workflow._jumpToStateFor(
        instance_tree, 'start_requested')
    return instance_tree

  def test_deleteFromRegularisationRequest_REQUESTdisallowed(self):
    self.assertRaises(
      Unauthorized,
      self.portal.InstanceTree_deleteFromRegularisationRequest,
      '',
      REQUEST={})

  def test_deleteFromRegularisationRequest_startedSubscription(self):
    project = self.addProject()
    person = self.makePerson(project, index=0, user=0)
    instance_tree = self.createInstanceTree(project)
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
    self.assertEqual(shared, False)

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

  def test_deleteFromRegularisationRequest_stoppedSubscription(self):
    project = self.addProject()
    person = self.makePerson(project, index=0, user=0)
    instance_tree = self.createInstanceTree(project)
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

  def test_deleteFromRegularisationRequest_destroyedSubscription(self):
    project = self.addProject()
    person = self.makePerson(project, index=0, user=0)
    instance_tree = self.createInstanceTree(project)
    instance_tree.edit(
      destination_section=person.getRelativeUrl(),
    )
    self.portal.portal_workflow._jumpToStateFor(
        instance_tree, 'destroy_requested')

    result = instance_tree.\
        InstanceTree_deleteFromRegularisationRequest(person.getRelativeUrl())

    self.assertEqual(result, False)

  def test_deleteFromRegularisationRequest_nonMatchingPerson(self):
    project = self.addProject()
    instance_tree = self.createInstanceTree(project)
    self.assertRaises(
      AssertionError,
      instance_tree.InstanceTree_deleteFromRegularisationRequest,
      'foobar')

