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
  SlapOSTestCaseMixin,SlapOSTestCaseMixinWithAbort, TemporaryAlarmScript, PinnedDateTime

from DateTime import DateTime
from App.Common import rfc1123_date


def getFakeSlapState():
  return "destroy_requested"

class TestCRMSkinsMixin(SlapOSTestCaseMixinWithAbort):

  def afterSetUp(self):
    SlapOSTestCaseMixinWithAbort.afterSetUp(self)
    self.project = self.addProject()
    self.person = self.makePerson(self.project, new_id=self.new_id,
                                  index=0, user=0)

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

class TestSlapOSSupportRequestModule_getMonitoringUrlList(TestCRMSkinsMixin):

  def test_SupportRequestModule_getMonitoringUrlList(self):
    module = self.portal.support_request_module
    # We assume here that several objects created by others tests don't influentiate
    # this test.
    self.assertEqual(module.SupportRequestModule_getMonitoringUrlList(), [])
    with TemporaryAlarmScript(self.portal, 'Item_getSubscriptionStatus', "'subscribed'"):
      instance_tree = self._makeInstanceTree(self.project)
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

  def test_ComputeNode_hasContactedRecently_newly_created(self):
    compute_node, _ = self._makeComputeNode(self.addProject())
    self.tic()
    has_contacted = compute_node.ComputeNode_hasContactedRecently()
    self.assertTrue(has_contacted)

  def test_ComputeNode_hasContactedRecently_no_data(self):
    with PinnedDateTime(self, DateTime()-32):
      compute_node, _ = self._makeComputeNode(self.addProject())
    self.tic()

    has_contacted = compute_node.ComputeNode_hasContactedRecently()
    self.assertFalse(has_contacted)

  def test_ComputeNode_hasContactedRecently_memcached(self):
    with PinnedDateTime(self, DateTime()-32):
      compute_node, _ = self._makeComputeNode(self.addProject())
    compute_node.setAccessStatus("")

    self.tic()

    has_contacted = compute_node.ComputeNode_hasContactedRecently()
    self.assertTrue(has_contacted)

  def test_ComputeNode_hasContactedRecently_memcached_oudated_no_spl(self):
    with PinnedDateTime(self, DateTime()-32):
      compute_node, _ = self._makeComputeNode(self.addProject())
      compute_node.setAccessStatus("")

    self.tic()

    has_contacted = compute_node.ComputeNode_hasContactedRecently()
    self.assertFalse(has_contacted)


class TestSlapOSisSupportRequestCreationClosed(TestCRMSkinsMixin):

  def afterSetUp(self):
    TestCRMSkinsMixin.afterSetUp(self)
    self.project = self.addProject()
    self._cancelTestSupportRequestList()
    self.clearCache()

  def test_ERP5Site_isSupportRequestCreationClosed(self):

    person = self.makePerson(self.project, user=0)
    other_person = self.makePerson(self.project, user=0)
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
    person = self.makePerson(self.project, user=0)
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
    person = self.makePerson(self.project, user=0)
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


class TestSlapOSHasError(SlapOSTestCaseMixin):

  def test_SoftwareInstance_hasReportedError(self):
    instance = self.portal.software_instance_module.newContent(
      portal_type="Software Instance",
      reference=self.generateNewId()
    )
    _, partition = self._makeComputeNode(self.addProject())

    error_date = DateTime()
    with PinnedDateTime(self, error_date):
      instance.setErrorStatus("")

    self.assertEqual(instance.SoftwareInstance_hasReportedError(), None)

    instance.setAggregateValue(partition)

    self.assertEqual(str(instance.SoftwareInstance_hasReportedError()), '#error ')

    instance.setAccessStatus("")
    self.assertEqual(instance.SoftwareInstance_hasReportedError(), None)

  def test_SoftwareInstallation_hasReportedError(self):
    installation = self.portal.software_installation_module.newContent()

    self.assertEqual(installation.SoftwareInstallation_hasReportedError(), None)

    error_date = DateTime()
    with PinnedDateTime(self, error_date):
      installation.setErrorStatus("")

    self.assertEqual(
      rfc1123_date(installation.SoftwareInstallation_hasReportedError()),
      rfc1123_date(error_date))
    installation.setBuildingStatus("")

    self.assertEqual(installation.SoftwareInstallation_hasReportedError(), None)


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
      #specialise=
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

    event.setDestination(person.getRelativeUrl())
    self.assertFalse(event.checkConsistency())


class TestSlapOSFolder_getTicketFeedUrl(TestCRMSkinsMixin):

  def _test(self, module):
    self.assertRaises(ValueError, module.Folder_getTicketFeedUrl)
    person = self.makePerson(self.project, user=1)
    self.addProjectProductionManagerAssignment(person, self.project)
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

