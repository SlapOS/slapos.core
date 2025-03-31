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
  TemporaryAlarmScript, simulate
import json

def getFakeSlapState():
  return "destroy_requested"

class TestPanelSkinsMixin(SlapOSTestCaseMixinWithAbort):

  def afterSetUp(self):
    SlapOSTestCaseMixinWithAbort.afterSetUp(self)
    self.project = self.addProject()

  def getDocumentOnPanelContext(self, document):
    web_site = self.portal.web_site_module.slapos_master_panel
    return web_site.restrictedTraverse(document.getRelativeUrl())

class TestSupportRequestModule_getRssFeedUrl(TestPanelSkinsMixin):

  def testSupportRequestModule_getRssFeedUrl(self):
    module = self.portal.support_request_module
    self.assertRaises(ValueError, module.SupportRequestModule_getRssFeedUrl)
    person = self.makePerson(self.project, user=1)
    self.addProjectProductionManagerAssignment(person, self.project)
    self.tic()

    self.login(person.getUserId())

    # Fail if not on website context.
    self.assertRaises(ValueError, module.SupportRequestModule_getRssFeedUrl)

    module = self.portal.web_site_module.slapos_master_panel.support_request_module
    url = module.SupportRequestModule_getRssFeedUrl()
    self.assertIn('feed', url)
    self.assertIn(
      self.portal.web_site_module.slapos_master_panel.feed.absolute_url(), url)
    self.assertIn('access_token_secret', url)
    self.assertIn('access_token=', url)

    self.tic()
    self.assertEqual(url, module.SupportRequestModule_getRssFeedUrl())

class TestBase_hasSlapOSProjectUserGroup(TestPanelSkinsMixin):

  def test_Base_hasSlapOSProjectUserGroup_invalid_context(self):
    self.assertRaises(ValueError,
      self.project.Base_hasSlapOSProjectUserGroup, project_relation='couscous')

  def test_Base_hasSlapOSProjectUserGroup_customer(self):
    # Assignment for customer is added automatically
    person = self.makePerson(self.project, user=1)
    self.tic()
    self.login(person.getUserId())

    self.assertFalse(self.project.Base_hasSlapOSProjectUserGroup())
    self.assertFalse(self.project.Base_hasSlapOSProjectUserGroup(agent=True))
    self.assertTrue(self.project.Base_hasSlapOSProjectUserGroup(customer=True))
    self.assertFalse(self.project.Base_hasSlapOSProjectUserGroup(manager=True))

  def test_Base_hasSlapOSProjectUserGroup_project_manager(self):
    # Assignment for customer is added automatically
    person = self.makePerson(self.project, user=1)
    self.addProjectProductionManagerAssignment(person, self.project)
    self.tic()
    self.login(person.getUserId())

    self.assertFalse(self.project.Base_hasSlapOSProjectUserGroup())
    self.assertFalse(self.project.Base_hasSlapOSProjectUserGroup(agent=True))
    self.assertTrue(self.project.Base_hasSlapOSProjectUserGroup(customer=True))
    self.assertTrue(self.project.Base_hasSlapOSProjectUserGroup(manager=True))

  def test_Base_hasSlapOSProjectUserGroup_agent(self):
    # Assignment for customer is added automatically
    person = self.makePerson(self.project, user=1)
    self.addProjectProductionAgentAssignment(person, self.project)
    self.tic()
    self.login(person.getUserId())

    self.assertFalse(self.project.Base_hasSlapOSProjectUserGroup())
    self.assertTrue(self.project.Base_hasSlapOSProjectUserGroup(agent=True))
    self.assertTrue(self.project.Base_hasSlapOSProjectUserGroup(customer=True))
    self.assertFalse(self.project.Base_hasSlapOSProjectUserGroup(manager=True))

  def test_Base_hasSlapOSProjectUserGroup_destination_project(self):
    # Assignment for customer is added automatically
    person = self.makePerson(self.project, user=1)
    self.addProjectProductionManagerAssignment(person, self.project)
    support_request = self.portal.support_request_module.newContent(
      portal_type='Support Request',
      title='TESTSUPPORTREQUEST-%s' % self.generateNewId(),
      destination_project_value=self.project
    )
    self.tic()
    self.login(person.getUserId())

    # Uses project_relation='context'
    self.assertFalse(support_request.Base_hasSlapOSProjectUserGroup(
     project_relation='source_project'))
    self.assertFalse(support_request.Base_hasSlapOSProjectUserGroup(
      project_relation='source_project', agent=True))
    self.assertFalse(support_request.Base_hasSlapOSProjectUserGroup(
      project_relation='source_project', customer=True))
    self.assertFalse(support_request.Base_hasSlapOSProjectUserGroup(
      project_relation='source_project', manager=True))

    self.assertFalse(support_request.Base_hasSlapOSProjectUserGroup(
      project_relation='destination_project'))
    self.assertFalse(support_request.Base_hasSlapOSProjectUserGroup(
      project_relation='destination_project', agent=True))
    self.assertTrue(support_request.Base_hasSlapOSProjectUserGroup(
      project_relation='destination_project', customer=True))
    self.assertTrue(support_request.Base_hasSlapOSProjectUserGroup(
      project_relation='destination_project', manager=True))

  def test_Base_hasSlapOSProjectUserGroup_source_project(self):
    # Assignment for customer is added automatically
    person = self.makePerson(self.project, user=1)
    self.addProjectProductionManagerAssignment(person, self.project)
    support_request = self.portal.support_request_module.newContent(
      portal_type='Support Request',
      title='TESTSUPPORTREQUEST-%s' % self.generateNewId(),
      source_project_value=self.project
    )
    self.tic()
    self.login(person.getUserId())

    # Uses project_relation='context'
    self.assertFalse(support_request.Base_hasSlapOSProjectUserGroup(
     project_relation='destination_project'))
    self.assertFalse(support_request.Base_hasSlapOSProjectUserGroup(
      project_relation='destination_project', agent=True))
    self.assertFalse(support_request.Base_hasSlapOSProjectUserGroup(
      project_relation='destination_project', customer=True))
    self.assertFalse(support_request.Base_hasSlapOSProjectUserGroup(
      project_relation='destination_project', manager=True))

    self.assertFalse(support_request.Base_hasSlapOSProjectUserGroup(
      project_relation='source_project'))
    self.assertFalse(support_request.Base_hasSlapOSProjectUserGroup(
      project_relation='source_project', agent=True))
    self.assertTrue(support_request.Base_hasSlapOSProjectUserGroup(
      project_relation='source_project', customer=True))
    self.assertTrue(support_request.Base_hasSlapOSProjectUserGroup(
      project_relation='source_project', manager=True))

  def test_Base_hasSlapOSProjectUserGroup_follow_up(self):
    # Assignment for customer is added automatically
    person = self.makePerson(self.project, user=1)
    self.addProjectProductionManagerAssignment(person, self.project)
    compute_node = self.portal.compute_node_module.newContent(
      portal_type='Compute Node',
      title='TESTCOMPUTERNODE-%s' % self.generateNewId(),
      follow_up_value=self.project
    )
    self.tic()
    self.login(person.getUserId())

    self.assertFalse(compute_node.Base_hasSlapOSProjectUserGroup(
      project_relation='follow_up'))
    self.assertFalse(compute_node.Base_hasSlapOSProjectUserGroup(
      project_relation='follow_up', agent=True))
    self.assertTrue(compute_node.Base_hasSlapOSProjectUserGroup(
      project_relation='follow_up', customer=True))
    self.assertTrue(compute_node.Base_hasSlapOSProjectUserGroup(
      project_relation='follow_up', manager=True))

  def test_Base_hasSlapOSProjectUserGroup_not_a_project(self):
    # Assignment for customer is added automatically
    person = self.makePerson(self.project, user=1)
    self.addProjectProductionAgentAssignment(person, self.project)
    self.tic()
    self.login(person.getUserId())

    # Uses project_relation='context'
    self.assertFalse(person.Base_hasSlapOSProjectUserGroup())
    self.assertFalse(person.Base_hasSlapOSProjectUserGroup(agent=True))
    self.assertFalse(person.Base_hasSlapOSProjectUserGroup(customer=True))
    self.assertFalse(person.Base_hasSlapOSProjectUserGroup(manager=True))


class TestPerson_getCertificate(TestPanelSkinsMixin):

  def test_Person_getCertificate_unauthorized(self):
    person = self.makePerson(self.project, user=1)
    self.assertEqual(1 , len(person.objectValues(portal_type="ERP5 Login")))

    self.assertEqual(person.Person_getCertificate(), {})
    self.assertEqual(self.portal.REQUEST.RESPONSE.getStatus(), 403)

  def test_Person_getCertificate(self):
    person = self.makePerson(self.project, user=1)
    self.assertEqual(1 , len(person.objectValues(portal_type="ERP5 Login")))

    self.login(person.getUserId())
    response_dict = json.loads(person.Person_getCertificate())
    self.assertEqual(1 , len(person.objectValues(portal_type="Certificate Login")))
    login = person.objectValues(portal_type="Certificate Login")[0]
    self.assertEqual("validated" , login.getValidationState())

    self.assertSameSet(response_dict.keys(), ["common_name", "certificate", "id", "key"])

    self.assertEqual(response_dict["id"], login.getDestinationReference())
    self.assertEqual(json.dumps(response_dict["common_name"]), json.dumps(login.getReference()))
    self.assertEqual(self.portal.REQUEST.RESPONSE.getStatus(), 200)

    new_response_dict = json.loads(person.Person_getCertificate())
    self.assertTrue(new_response_dict)

    self.assertEqual(2 , len(person.objectValues(portal_type="Certificate Login")))
    new_login = [i for i in person.objectValues(portal_type="Certificate Login")
      if i.getUid() != login.getUid()][0]

    self.assertEqual("validated" , login.getValidationState())
    self.assertEqual("validated" , new_login.getValidationState())
    self.assertNotEqual(login.getReference(), new_login.getReference())
    self.assertNotEqual(login.getDestinationReference(), new_login.getDestinationReference())

    self.assertSameSet(new_response_dict.keys(), ["common_name", "certificate", "id", "key"])
    self.assertEqual(json.dumps(new_response_dict["common_name"]), json.dumps(new_login.getReference()))
    self.assertEqual(new_response_dict["id"], new_login.getDestinationReference())

    self.assertNotEqual(new_response_dict["common_name"], response_dict["common_name"])
    self.assertNotEqual(new_response_dict["id"], response_dict["id"])
    self.assertNotEqual(new_response_dict["key"], response_dict["key"])
    self.assertNotEqual(new_response_dict["certificate"], response_dict["certificate"])

    self.assertEqual(self.portal.REQUEST.RESPONSE.getStatus(), 200)

class TestBase_hasSlapOSAccountingUserGroup(TestPanelSkinsMixin):

  def _makePersonAndRegularisationRequest(self):
    person = self.makePerson(self.project, user=1)
    regularisation_request = self.portal.regularisation_request_module.newContent(
      portal_type='Regularisation Request',
      title='TESTREGREQ-%s' % self.generateNewId(),
      destination_decision_value=person
    )
    regularisation_request.submit()
    return person, regularisation_request

  def test_Base_hasSlapOSAccountingUserGroup_no_user(self):
    self.logout()
    self.assertFalse(self.project.Base_hasSlapOSAccountingUserGroup())
    self.login()
    self.assertFalse(self.project.Base_hasSlapOSAccountingUserGroup())

  def test_Base_hasSlapOSAccountingUserGroup_no_access(self):
    person, regularisation_request = self._makePersonAndRegularisationRequest()
    self.addProjectProductionManagerAssignment(person, self.project)
    self.tic()
    self.login(person.getUserId())

    self.assertFalse(regularisation_request.Base_hasSlapOSAccountingUserGroup())
    self.assertFalse(regularisation_request.Base_hasSlapOSAccountingUserGroup(
      agent=True))
    self.assertFalse(regularisation_request.Base_hasSlapOSAccountingUserGroup(
      manager=True))

  def test_Base_hasSlapOSAccountingUserGroup_sale_manager(self):
    person, regularisation_request = self._makePersonAndRegularisationRequest()
    self.addSaleManagerAssignment(person)
    self.tic()
    self.login(person.getUserId())

    self.assertFalse(regularisation_request.Base_hasSlapOSAccountingUserGroup())
    self.assertTrue(regularisation_request.Base_hasSlapOSAccountingUserGroup(
      manager=True))
    self.assertFalse(regularisation_request.Base_hasSlapOSAccountingUserGroup(
      agent=True))
    self.assertTrue(regularisation_request.Base_hasSlapOSAccountingUserGroup(
      manager=True, agent=True))

  def test_Base_hasSlapOSAccountingUserGroup_sale_agent(self):
    person, regularisation_request = self._makePersonAndRegularisationRequest()
    self.addSaleAgentAssignment(person)
    self.tic()
    self.login(person.getUserId())

    self.assertFalse(regularisation_request.Base_hasSlapOSAccountingUserGroup())
    self.assertFalse(regularisation_request.Base_hasSlapOSAccountingUserGroup(
      manager=True))
    self.assertTrue(regularisation_request.Base_hasSlapOSAccountingUserGroup(
      agent=True))
    self.assertTrue(regularisation_request.Base_hasSlapOSAccountingUserGroup(
      manager=True, agent=True))

  def test_Base_hasSlapOSAccountingUserGroup_accounting_manager(self):
    person, regularisation_request = self._makePersonAndRegularisationRequest()
    self.addAccountingManagerAssignment(person)
    self.tic()
    self.login(person.getUserId())

    self.assertFalse(regularisation_request.Base_hasSlapOSAccountingUserGroup())
    self.assertTrue(regularisation_request.Base_hasSlapOSAccountingUserGroup(
      manager=True))
    self.assertFalse(regularisation_request.Base_hasSlapOSAccountingUserGroup(
      agent=True))
    self.assertTrue(regularisation_request.Base_hasSlapOSAccountingUserGroup(
      manager=True, agent=True))

  def test_Base_hasSlapOSAccountingUserGroup_accounting_agent(self):
    person, regularisation_request = self._makePersonAndRegularisationRequest()
    self.addAccountingAgentAssignment(person)
    self.tic()
    self.login(person.getUserId())

    self.assertFalse(regularisation_request.Base_hasSlapOSAccountingUserGroup())
    self.assertFalse(regularisation_request.Base_hasSlapOSAccountingUserGroup(
      manager=True))
    self.assertTrue(regularisation_request.Base_hasSlapOSAccountingUserGroup(
      agent=True))
    self.assertTrue(regularisation_request.Base_hasSlapOSAccountingUserGroup(
      manager=True, agent=True))

class TestTicket_validateSlapOS(TestPanelSkinsMixin):

  def _makePersonAndTicket(self, portal_type):
    person = self.makePerson(self.project, user=1)
    ticket = self.portal.getDefaultModule(portal_type).newContent(
      portal_type=portal_type,
      title='TESTICKET-%s' % self.generateNewId(),
      destination_decision_value=person
    )
    return person, ticket

  def test_Ticket_validateSlapOS_regularisation_request(self):
    person, ticket = self._makePersonAndTicket('Regularisation Request')
    ticket.submit()
    self.addAccountingManagerAssignment(person)
    self.tic()
    self.login(person.getUserId())
    ticket.Ticket_validateSlapOS()
    self.assertEqual(ticket.getSimulationState(), 'submitted')
    ticket.validate()
    ticket.suspend()
    ticket.Ticket_validateSlapOS()
    self.assertEqual(ticket.getSimulationState(), 'validated')
    ticket.Ticket_validateSlapOS()
    self.assertEqual(ticket.getSimulationState(), 'validated')
    ticket.invalidate()
    ticket.Ticket_validateSlapOS()
    self.assertEqual(ticket.getSimulationState(), 'invalidated')

  def test_Ticket_validateSlapOS_support_request(self):
    person, ticket = self._makePersonAndTicket('Support Request')
    ticket.edit(
      source_project_value=self.project,
      destination_project_value=self.project)
    ticket.submit()
    self.addProjectProductionManagerAssignment(person, self.project)
    self.tic()
    self.login(person.getUserId())

    # Cheat to call the script wont change the value.
    ticket.Ticket_validateSlapOS()
    self.assertEqual(ticket.getSimulationState(), 'submitted')
    ticket.validate()
    ticket.suspend()
    self.login(person.getUserId())
    ticket.Ticket_validateSlapOS()
    self.assertEqual(ticket.getSimulationState(), 'suspended')
    ticket.validate()
    ticket.Ticket_validateSlapOS()
    self.assertEqual(ticket.getSimulationState(), 'validated')
    ticket.invalidate()
    ticket.Ticket_validateSlapOS()
    self.assertEqual(ticket.getSimulationState(), 'invalidated')

class TestTicket_suspendSlapOS(TestPanelSkinsMixin):

  def _makePersonAndTicket(self, portal_type):
    person = self.makePerson(self.project, user=1)
    ticket = self.portal.getDefaultModule(portal_type).newContent(
      portal_type=portal_type,
      title='TESTICKET-%s' % self.generateNewId(),
      destination_decision_value=person
    )
    return person, ticket

  def test_Ticket_suspendSlapOS_regularisation_request(self):
    person, ticket = self._makePersonAndTicket('Regularisation Request')
    ticket.submit()
    self.addAccountingManagerAssignment(person)
    self.tic()
    self.login(person.getUserId())
    ticket.Ticket_suspendSlapOS()
    self.assertEqual(ticket.getSimulationState(), 'submitted')
    ticket.validate()
    ticket.Ticket_suspendSlapOS()
    self.assertEqual(ticket.getSimulationState(), 'suspended')
    ticket.Ticket_suspendSlapOS()
    self.assertEqual(ticket.getSimulationState(), 'suspended')
    ticket.validate()
    ticket.invalidate()
    ticket.Ticket_suspendSlapOS()
    self.assertEqual(ticket.getSimulationState(), 'invalidated')

  def test_Ticket_suspendSlapOS_support_request(self):
    person, ticket = self._makePersonAndTicket('Support Request')
    ticket.edit(
      source_project_value=self.project,
      destination_project_value=self.project)
    ticket.submit()
    self.addProjectProductionManagerAssignment(person, self.project)
    self.tic()
    self.login(person.getUserId())
    ticket.Ticket_suspendSlapOS()
    self.assertEqual(ticket.getSimulationState(), 'submitted')
    ticket.validate()
    ticket.Ticket_suspendSlapOS()
    self.assertEqual(ticket.getSimulationState(), 'suspended')
    ticket.Ticket_suspendSlapOS()
    self.assertEqual(ticket.getSimulationState(), 'suspended')
    ticket.validate()
    ticket.invalidate()
    ticket.Ticket_suspendSlapOS()
    self.assertEqual(ticket.getSimulationState(), 'invalidated')

class TestTicket_closeSlapOS(TestPanelSkinsMixin):

  def _makePersonAndTicket(self, portal_type):
    person = self.makePerson(self.project, user=1)
    ticket = self.portal.getDefaultModule(portal_type).newContent(
      portal_type=portal_type,
      title='TESTICKET-%s' % self.generateNewId(),
      destination_decision_value=person
    )
    return person, ticket

  def test_Ticket_closeSlapOS_support_request(self):
    person, ticket = self._makePersonAndTicket('Support Request')
    ticket.edit(
      source_project_value=self.project,
      destination_project_value=self.project)
    ticket.submit()
    self.addProjectProductionManagerAssignment(person, self.project)
    self.tic()
    self.login(person.getUserId())
    self.assertEqual(ticket.getSimulationState(), 'submitted')
    ticket.validate()
    ticket.Ticket_closeSlapOS("x")
    self.assertEqual(ticket.getSimulationState(), 'invalidated')
    ticket.validate()
    ticket.suspend()
    ticket.Ticket_closeSlapOS("x")
    self.assertEqual(ticket.getSimulationState(), 'invalidated')
    ticket.Ticket_closeSlapOS("x")
    self.assertEqual(ticket.getSimulationState(), 'invalidated')

class TestInstanceTree_redirectToManualDepositPayment(TestPanelSkinsMixin):

  def addNonSubscribedInstanceTree(self, project, person,
                                   software_release, software_type,
                                   shared=False):
    request_kw = dict(
      software_release=software_release,
      software_title=self.generateNewSoftwareTitle(),
      software_type=software_type,
      instance_xml=self.generateSafeXml(),
      sla_xml=self.generateEmptyXml(),
      shared=shared,
      state="started",
      project_reference=project.getReference()
    )
    person.requestSoftwareInstance(**request_kw)
    return person.REQUEST.get('request_instance_tree')

  def _testInstanceTree_redirectToManualDepositPayment_no_subscription(self):
    _, release_variation, type_variation, _, _, instance_tree = \
      self.bootstrapAllocableInstanceTree(is_accountable=True, base_price=5)
    self.tic()

    person = instance_tree.getDestinationSectionValue()
    project = instance_tree.getFollowUpValue()
    self.assertNotEqual(person, None)
    self.assertNotEqual(project, None)

    # Don't trigger the alarms to emulate the subscription request is not
    # found yet
    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm', "'disabled'",
                              attribute='comment'):
      instance_tree = self.addNonSubscribedInstanceTree(
        project, person, release_variation.getUrlString(),
        type_variation.getTitle())
      self.tic()

    self.assertNotEqual(instance_tree, None)

    subscription_request = self.portal.portal_catalog.getResultValue(
      portal_type='Subscription Request',
      aggregate__uid=instance_tree.getUid())
    self.assertEqual(subscription_request, None)

    self.login(person.getUserId())

    return self.getDocumentOnPanelContext(instance_tree)

  def testInstanceTree_redirectToManualDepositPayment_no_subscription(self):
    instance_tree_on_website = self._testInstanceTree_redirectToManualDepositPayment_no_subscription()
    # This script only works on website context, and shoult not raise and return
    # a redirect.
    response = instance_tree_on_website.InstanceTree_redirectToManualDepositPayment()
    self.assertIn('?page=slapos_master_panel_external_payment_result', response)

  @simulate("PaymentTransaction_triggerPaymentCheckAlarmAndRedirectToPanel",
            "*args, **kwargs",
            "return context")
  def testInstanceTree_redirectToManualDepositPayment_no_subscription_with_simulate(self):
    instance_tree_on_website = self._testInstanceTree_redirectToManualDepositPayment_no_subscription()
    self.tic()
    payment_transaction = instance_tree_on_website.InstanceTree_redirectToManualDepositPayment()
    self.login()
    # Virtual Master subscription request + Instance Tree subscription request = -10
    self.assertEqual(payment_transaction.PaymentTransaction_getTotalPayablePrice(),
                     -10)

  def _testInstanceTree_redirectToManualDepositPayment(self):
    _, release_variation, type_variation, _, _, instance_tree = \
      self.bootstrapAllocableInstanceTree(is_accountable=True, base_price=5)
    self.tic()

    person = instance_tree.getDestinationSectionValue()
    project = instance_tree.getFollowUpValue()
    self.assertNotEqual(person, None)
    self.assertNotEqual(project, None)

    instance_tree = self.addNonSubscribedInstanceTree(
      project, person, release_variation.getUrlString(),
      type_variation.getTitle())
    self.tic()

    self.assertNotEqual(instance_tree, None)

    subscription_request = self.portal.portal_catalog.getResultValue(
      portal_type='Subscription Request',
      aggregate__uid=instance_tree.getUid())
    self.assertNotEqual(subscription_request, None)

    self.login(person.getUserId())

    return self.getDocumentOnPanelContext(instance_tree)


  def testInstanceTree_redirectToManualDepositPayment(self):
    instance_tree_on_website = self._testInstanceTree_redirectToManualDepositPayment()
    # This script only works on website context, and shoult not raise and return
    # a redirect.
    response = instance_tree_on_website.InstanceTree_redirectToManualDepositPayment()
    self.assertIn('?page=slapos_master_panel_external_payment_result', response)


  @simulate("PaymentTransaction_triggerPaymentCheckAlarmAndRedirectToPanel", "*args, **kwargs",
              "return context")
  def testInstanceTree_redirectToManualDepositPayment_with_simulate(self):
    instance_tree_on_website = self._testInstanceTree_redirectToManualDepositPayment()
    self.tic()
    payment_transaction = instance_tree_on_website.InstanceTree_redirectToManualDepositPayment()
    self.login()
    # Virtual Master subscription request + Instance Tree subscription request = -10
    self.assertEqual(payment_transaction.PaymentTransaction_getTotalPayablePrice(),
                     -10)


