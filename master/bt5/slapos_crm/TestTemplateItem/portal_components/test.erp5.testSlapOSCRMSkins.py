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
  SlapOSTestCaseMixin,SlapOSTestCaseMixinWithAbort
from Products.ERP5Type.tests.utils import FileUpload
import os

from zExceptions import Unauthorized


def getFakeSlapState():
  return "destroy_requested"

class TestCRMSkinsMixin(SlapOSTestCaseMixinWithAbort):

  def afterSetUp(self):
    SlapOSTestCaseMixinWithAbort.afterSetUp(self)
    self.project = self.addProject()
    self.person = self.makePerson(self.project, new_id=self.new_id,
                                  index=0, user=0)

  def _makeInstanceTree(self, project):
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
        follow_up_value=project
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
    self._makeComputeNode(self.project)
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

class TestSlapOSisSupportRequestCreationClosed(TestCRMSkinsMixin):

  def afterSetUp(self):
    TestCRMSkinsMixin.afterSetUp(self)
    self.project = self.addProject()
    self.other_project = self.addProject()
    # ensure it is set to 5
    self.portal.portal_preferences.slapos_default_system_preference\
      .setPreferredSupportRequestCreationLimit(5)
    self.clearCache()

  def newDummySupportRequest(self,
                             resource="service_module/slapos_crm_monitoring",
                             state='validated'):
    sr = self.portal.support_request_module.newContent(\
      title="Test isSupportRequestCreationClosed %s" % self.generateNewId(),
      resource=resource,
      source_project_value=self.project)
    if state == 'validated':
      sr.validate()
    elif state == 'suspended':
      sr.validate()
      sr.suspend()
    elif state == 'submited':
      sr.submit()
    sr.immediateReindexObject()

  def test_Project_isSupportRequestCreationClosed(self, state='validated'):
    self.assertFalse(self.project.Project_isSupportRequestCreationClosed())
    self.newDummySupportRequest(state=state)
    self.assertFalse(self.project.Project_isSupportRequestCreationClosed())
    self.newDummySupportRequest(state=state)
    self.assertFalse(self.project.Project_isSupportRequestCreationClosed())
    self.newDummySupportRequest(state=state)
    self.assertFalse(self.project.Project_isSupportRequestCreationClosed())
    self.newDummySupportRequest(state=state)
    self.assertFalse(self.project.Project_isSupportRequestCreationClosed())
    self.newDummySupportRequest(state=state)
    self.assertTrue(self.project.Project_isSupportRequestCreationClosed())
    self.newDummySupportRequest(state=state)
    self.assertTrue(self.project.Project_isSupportRequestCreationClosed())
    # it dont close another project
    self.assertFalse(self.other_project.Project_isSupportRequestCreationClosed())

  def test_Project_isSupportRequestCreationClosed_submited_state(self):
    self.test_Project_isSupportRequestCreationClosed(state='submited')

  def test_Project_isSupportRequestCreationClosed_suspended_state(self):
    self.test_Project_isSupportRequestCreationClosed(state='suspended')

  def test_Project_isSupportRequestCreationClosed_nonmonitoring(self):
    self.assertFalse(self.project.Project_isSupportRequestCreationClosed())
    self.newDummySupportRequest(resource='')
    self.assertFalse(self.project.Project_isSupportRequestCreationClosed())
    self.newDummySupportRequest(resource='')
    self.assertFalse(self.project.Project_isSupportRequestCreationClosed())
    self.newDummySupportRequest(resource='')
    self.assertFalse(self.project.Project_isSupportRequestCreationClosed())
    self.newDummySupportRequest(resource='')
    self.assertFalse(self.project.Project_isSupportRequestCreationClosed())
    self.newDummySupportRequest(resource='')
    self.assertFalse(self.project.Project_isSupportRequestCreationClosed())
    self.newDummySupportRequest(resource='')
    self.assertFalse(self.project.Project_isSupportRequestCreationClosed())
    self.newDummySupportRequest(resource='')
    self.assertFalse(self.project.Project_isSupportRequestCreationClosed())
    # it dont close another project
    self.assertFalse(self.other_project.Project_isSupportRequestCreationClosed())

class TestCRMPropertySheetConstraint(SlapOSTestCaseMixin):

  def afterSetUp(self):
    SlapOSTestCaseMixin.afterSetUp(self)
    portal = self.getPortalObject()
    self.project = self.addProject()

    person_user = self.makePerson(self.project)
    self.tic()

    # Login as new user
    self.login(person_user.getUserId())

    new_person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()
    self.assertEqual(person_user.getRelativeUrl(), new_person.getRelativeUrl())

    self.support_request = portal.support_request_module.newContent(
      portal_type="Support Request",
      destination_value=person_user,
      destination_decision_value=person_user,
    )

    # Value set by the init
    self.assertTrue(self.support_request.getReference().startswith("SR-"),
      "Reference don't start with SR- : %s" % self.support_request.getReference())

  def beforeTearDown(self):
    transaction.abort()

  def testCheckCustomerAsSourceOrDestinationConsistency(self):
    person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()

    self.support_request.Ticket_createProjectEvent(
      "foo", "incoming", "Web Message",
      self.portal.service_module.slapos_crm_information.getRelativeUrl(),
      "bar", "text/plain"
    )
    self.tic()

    self.logout()
    self.login()

    event = self.support_request.getFollowUpRelatedValue()
    self.assertNotEqual(event, None)

    self.assertFalse(event.checkConsistency())
    self.assertFalse(self.support_request.checkConsistency())

    person_user = self.makePerson(self.project)
    self.tic()

    event.setSource(person_user.getRelativeUrl())

    non_consistency_list = [str(i.getTranslatedMessage()) for i in event.checkConsistency()]
    self.assertEqual(non_consistency_list, [
      'Customer should be source or destination of the event'
    ])

    # Check script in case
    non_consistency_list = event.Event_checkCustomerAsSourceOrDestinationConsistency()
    self.assertEqual(non_consistency_list, [
      'Customer should be source or destination of the event'
    ])

    event.setDestination(person.getRelativeUrl())
    self.assertFalse(event.checkConsistency())
    # Check script in case
    self.assertEqual([],
      event.Event_checkCustomerAsSourceOrDestinationConsistency())

class TestProject_createSupportRequestWithCausality(TestCRMSkinsMixin):

  def testProject_createSupportRequestWithCausality(self):
    self._makeComputeNode(self.project)
    self._makeComplexComputeNode(self.project)

    new_id = self.generateNewId()
    title = "TestProject_createSupportRequestWithCausality title %s" % (new_id)
    text_content = "Test Description %s" % (new_id)

    ticket = self.project.Project_createSupportRequestWithCausality(
      title=title,
      text_content=text_content,
      causality=self.compute_node.getRelativeUrl(),
      destination_decision=self.person.getRelativeUrl())

    self.assertNotEqual(ticket, None)
    self.assertEqual(ticket.getSimulationState(), 'submitted')
    self.assertEqual(ticket.getTitle(), title)

    self.tic()

    self.assertEqual(None,
      self.project.Project_createSupportRequestWithCausality(
        title=title,
        text_content=text_content,
        causality=self.compute_node.getRelativeUrl(),
        destination_decision=self.person.getRelativeUrl()))

    self.assertEqual(None,
      self.project.Project_createSupportRequestWithCausality(
        title="Some other title",
        text_content="Some other content",
        causality=self.compute_node.getRelativeUrl(),
        destination_decision=self.person.getRelativeUrl()))

    # Same tittle different causality
    ticket = self.project.Project_createSupportRequestWithCausality(
      title=title,
      text_content=text_content,
      causality=self.start_requested_software_instance.getSpecialise(),
      destination_decision=self.person.getRelativeUrl())

    self.assertNotEqual(ticket, None)
    self.assertEqual(ticket.getSimulationState(), 'submitted')
    self.assertEqual(ticket.getTitle(), title)

    self.tic()

    self.assertEqual(None,
      self.project.Project_createSupportRequestWithCausality(
        title="Some other title",
        text_content="Some other content",
        causality=self.start_requested_software_instance.getSpecialise(),
        destination_decision=self.person.getRelativeUrl()))


class TestTicket_createProjectEvent(TestCRMSkinsMixin):

  def createUsualTicket(self):
    portal = self.portal
    return portal.support_request_module.newContent(
      portal_type='Support Request',
      title='test support request',
      source_value=portal.person_module.newContent(
        portal_type='Person',
        title='ticket source person'
      ),
      source_section_value=portal.organisation_module.newContent(
        portal_type='Organisation',
        title='ticket source section organisation'
      ),
      source_project_value=portal.project_module.newContent(
        portal_type='Project',
        title='ticket source project'
      ),
      destination_value=portal.person_module.newContent(
        portal_type='Person',
        title='ticket destination person'
      ),
      destination_section_value=portal.organisation_module.newContent(
        portal_type='Organisation',
        title='ticket destination section organisation'
      ),
      destination_project_value=portal.project_module.newContent(
        portal_type='Project',
        title='ticket destination project'
      ),
    )

  def makeImageFileUpload(self):
    import Products.ERP5.tests
    file_upload = FileUpload(
            os.path.join(os.path.dirname(Products.ERP5.tests.__file__),
            'test_data', 'images', 'erp5_logo.png'))
    file_upload.headers['Content-Type'] = 'image/png'
    return file_upload

  def assertSameEventAttachmentList(self, event, information_dict_list=None):
    if information_dict_list is None:
      information_dict_list = []

    event_information_dict_list = []
    for information in event.getAttachmentInformationList():
      if information['uid'] != information['filename']:
        event_information_dict_list.append({
          'title': information['filename'],
          'content_type': information['content_type'],
          'index': information['index']
        })

    import json
    self.assertSameSet(
      [json.dumps(x) for x in event_information_dict_list],
      [json.dumps(x) for x in information_dict_list]
    )

  def test_Ticket_createProjectEvent_REQUEST_disallowed(self):
    ticket = self.createUsualTicket()
    self.assertRaises(
      Unauthorized,
      ticket.Ticket_createProjectEvent,
      'foo_title', 'foo_direction', 'foo portal type',
      'foo resource', 'foo text',
      REQUEST={})

  def test_Ticket_createProjectEvent_incomingEventWithoutAttachment(self):
    ticket = self.createUsualTicket()
    event = ticket.Ticket_createProjectEvent(
      'foo_title', 'incoming', 'Letter',
      'foo resource', 'foo text',
    )
    self.assertEquals(event.getPortalType(), 'Letter')
    self.assertEquals(event.getTitle(), 'foo_title')
    self.assertEquals(event.getFollowUp(), ticket.getRelativeUrl())
    self.assertEquals(event.getResource(), 'foo resource')
    self.assertEquals(event.getSource(), ticket.getDestination())
    self.assertEquals(event.getSourceSection(), ticket.getDestinationSection())
    self.assertEquals(event.getSourceProject(), ticket.getDestinationProject())
    self.assertEquals(event.getDestination(), ticket.getSource())
    self.assertEquals(event.getDestinationSection(), ticket.getSourceSection())
    self.assertEquals(event.getDestinationProject(), ticket.getSourceProject())
    self.assertEquals(event.getTextContent(), 'foo text')
    self.assertEquals(event.getContentType(), 'text/plain')
    self.assertSameEventAttachmentList(event)
    self.assertEquals(event.getSimulationState(), 'stopped')

  def test_Ticket_createProjectEvent_incomingEventWithoutAttachmentAndNotExistingNotificationMessage(self):
    ticket = self.createUsualTicket()
    event = ticket.Ticket_createProjectEvent(
      'foo_title', 'incoming', 'Letter',
      'foo resource', 'foo text',
      notification_message='foo notification message'
    )
    self.assertEquals(event.getPortalType(), 'Letter')
    self.assertEquals(event.getTitle(), 'foo_title')
    self.assertEquals(event.getFollowUp(), ticket.getRelativeUrl())
    self.assertEquals(event.getResource(), 'foo resource')
    self.assertEquals(event.getSource(), ticket.getDestination())
    self.assertEquals(event.getSourceSection(), ticket.getDestinationSection())
    self.assertEquals(event.getSourceProject(), ticket.getDestinationProject())
    self.assertEquals(event.getDestination(), ticket.getSource())
    self.assertEquals(event.getDestinationSection(), ticket.getSourceSection())
    self.assertEquals(event.getDestinationProject(), ticket.getSourceProject())
    self.assertEquals(event.getTextContent(), 'foo text')
    self.assertEquals(event.getContentType(), 'text/plain')
    self.assertSameEventAttachmentList(event)
    self.assertEquals(event.getSimulationState(), 'stopped')

  def test_Ticket_createProjectEvent_incomingEventWithoutAttachmentAndNotificationMessage(self):
    ticket = self.createUsualTicket()
    notification_message = self.portal.notification_message_module.newContent(
      portal_type='Notification Message',
      reference='notification-reference-%s' % self.generateNewId(),
      language='en',
      version='001',
      title='foo notification title',
      text_content='<p>foo notification text content</p>',
      content_type='text/html'
    )
    notification_message.validate()
    self.tic()
    event = ticket.Ticket_createProjectEvent(
      'foo_title', 'incoming', 'Letter',
      'foo resource', 'foo text',
      notification_message=notification_message.getReference(),
      language=notification_message.getLanguage()
    )
    self.assertEquals(event.getPortalType(), 'Letter')
    self.assertEquals(event.getTitle(), notification_message.getTitle())
    self.assertEquals(event.getFollowUp(), ticket.getRelativeUrl())
    self.assertEquals(event.getResource(), 'foo resource')
    self.assertEquals(event.getSource(), ticket.getDestination())
    self.assertEquals(event.getSourceSection(), ticket.getDestinationSection())
    self.assertEquals(event.getSourceProject(), ticket.getDestinationProject())
    self.assertEquals(event.getDestination(), ticket.getSource())
    self.assertEquals(event.getDestinationSection(), ticket.getSourceSection())
    self.assertEquals(event.getDestinationProject(), ticket.getSourceProject())
    self.assertEquals(event.getTextContent(), notification_message.getTextContent())
    self.assertEquals(event.getContentType(), notification_message.getContentType())
    self.assertSameEventAttachmentList(event)
    self.assertEquals(event.getSimulationState(), 'stopped')

  def test_Ticket_createProjectEvent_incomingEventWithSourceAndDestination(self):
    ticket = self.createUsualTicket()
    source_value = self.portal.person_module.newContent(
      portal_type='Person',
      title='custom source person'
    )
    destination_value = self.portal.person_module.newContent(
      portal_type='Person',
      title='custom destination person'
    )
    event = ticket.Ticket_createProjectEvent(
      'foo_title', 'incoming', 'Letter',
      'foo resource', 'foo text',
      source=source_value.getRelativeUrl(),
      destination=destination_value.getRelativeUrl()
    )
    self.assertEquals(event.getPortalType(), 'Letter')
    self.assertEquals(event.getTitle(), 'foo_title')
    self.assertEquals(event.getFollowUp(), ticket.getRelativeUrl())
    self.assertEquals(event.getResource(), 'foo resource')
    self.assertEquals(event.getSource(), source_value.getRelativeUrl())
    self.assertEquals(event.getSourceSection(), ticket.getDestinationSection())
    self.assertEquals(event.getSourceProject(), ticket.getDestinationProject())
    self.assertEquals(event.getDestination(), destination_value.getRelativeUrl())
    self.assertEquals(event.getDestinationSection(), ticket.getSourceSection())
    self.assertEquals(event.getDestinationProject(), ticket.getSourceProject())
    self.assertEquals(event.getTextContent(), 'foo text')
    self.assertEquals(event.getContentType(), 'text/plain')
    self.assertSameEventAttachmentList(event)
    self.assertEquals(event.getSimulationState(), 'stopped')

  def test_Ticket_createProjectEvent_incomingEventWithAttachment(self):
    ticket = self.createUsualTicket()
    event = ticket.Ticket_createProjectEvent(
      'foo_title', 'incoming', 'Web Message',
      'foo resource', 'foo text',
      attachment=self.makeImageFileUpload()
    )
    self.assertEquals(event.getPortalType(), 'Web Message')
    self.assertEquals(event.getTitle(), 'foo_title')
    self.assertEquals(event.getFollowUp(), ticket.getRelativeUrl())
    self.assertEquals(event.getResource(), 'foo resource')
    self.assertEquals(event.getSource(), ticket.getDestination())
    self.assertEquals(event.getSourceSection(), ticket.getDestinationSection())
    self.assertEquals(event.getSourceProject(), ticket.getDestinationProject())
    self.assertEquals(event.getDestination(), ticket.getSource())
    self.assertEquals(event.getDestinationSection(), ticket.getSourceSection())
    self.assertEquals(event.getDestinationProject(), ticket.getSourceProject())
    self.assertEquals(event.getTextContent(), 'foo text')
    self.assertEquals(event.getContentType(), 'text/plain')
    self.assertSameEventAttachmentList(event, [{
      "index": 2,
      "content_type": "image/png",
      "title": "erp5_logo.png"
    }])
    self.assertEquals(event.getSimulationState(), 'stopped')

  def test_Ticket_createProjectEvent_incomingEventWithAttachmentAndNotificationMessage(self):
    ticket = self.createUsualTicket()
    self.assertRaises(
      ValueError,
      ticket.Ticket_createProjectEvent,
      'foo_title', 'incoming', 'foo portal type',
      'foo resource', 'foo text',
      notification_message='foo notification reference',
      attachment=self.makeImageFileUpload()
    )

  def test_Ticket_createProjectEvent_outgoingEvent(self):
    ticket = self.createUsualTicket()
    event = ticket.Ticket_createProjectEvent(
      'foo_title', 'outgoing', 'Web Message',
      'foo resource', 'foo text',
    )
    self.assertEquals(event.getPortalType(), 'Web Message')
    self.assertEquals(event.getTitle(), 'foo_title')
    self.assertEquals(event.getFollowUp(), ticket.getRelativeUrl())
    self.assertEquals(event.getResource(), 'foo resource')
    self.assertEquals(event.getDestination(), ticket.getDestination())
    self.assertEquals(event.getDestinationSection(), ticket.getDestinationSection())
    self.assertEquals(event.getDestinationProject(), ticket.getDestinationProject())
    self.assertEquals(event.getSource(), ticket.getSource())
    self.assertEquals(event.getSourceSection(), ticket.getSourceSection())
    self.assertEquals(event.getSourceProject(), ticket.getSourceProject())
    self.assertEquals(event.getTextContent(), 'foo text')
    self.assertEquals(event.getContentType(), 'text/plain')
    self.assertSameEventAttachmentList(event)
    self.assertEquals(event.getSimulationState(), 'delivered')

  def test_Ticket_createProjectEvent_outgoingEventWithSourceAndDestination(self):
    ticket = self.createUsualTicket()
    source_value = self.portal.person_module.newContent(
      portal_type='Person',
      title='custom source person'
    )
    destination_value = self.portal.person_module.newContent(
      portal_type='Person',
      title='custom destination person'
    )
    event = ticket.Ticket_createProjectEvent(
      'foo_title', 'outgoing', 'Web Message',
      'foo resource', 'foo text',
      source=source_value.getRelativeUrl(),
      destination=destination_value.getRelativeUrl()
    )
    self.assertEquals(event.getPortalType(), 'Web Message')
    self.assertEquals(event.getTitle(), 'foo_title')
    self.assertEquals(event.getFollowUp(), ticket.getRelativeUrl())
    self.assertEquals(event.getResource(), 'foo resource')
    self.assertEquals(event.getDestination(), destination_value.getRelativeUrl())
    self.assertEquals(event.getDestinationSection(), ticket.getDestinationSection())
    self.assertEquals(event.getDestinationProject(), ticket.getDestinationProject())
    self.assertEquals(event.getSource(), source_value.getRelativeUrl())
    self.assertEquals(event.getSourceSection(), ticket.getSourceSection())
    self.assertEquals(event.getSourceProject(), ticket.getSourceProject())
    self.assertEquals(event.getTextContent(), 'foo text')
    self.assertEquals(event.getContentType(), 'text/plain')
    self.assertSameEventAttachmentList(event)
    self.assertEquals(event.getSimulationState(), 'delivered')

