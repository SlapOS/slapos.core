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

from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixinWithAbort
import json

def getFakeSlapState():
  return "destroy_requested"

class TestPanelSkinsMixin(SlapOSTestCaseMixinWithAbort):

  def afterSetUp(self):
    SlapOSTestCaseMixinWithAbort.afterSetUp(self)
    self.project = self.addProject()


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

class TestBase_hasSlapOSAccountingUserGroup(TestPanelSkinsMixin):

  def test_Base_hasSlapOSAccountingUserGroup_invalid_context(self):
    self.assertRaises(ValueError,
      self.project.Base_hasSlapOSAccountingUserGroup,
      customer_relation='context')

  def test_Base_hasSlapOSAccountingUserGroup(self):
    # Assignment for customer is added automatically
    person = self.makePerson(self.project, user=1)
    self.addProjectProductionManagerAssignment(person, self.project)
    self.tic()

    subscription_request = self.portal.subscription_request_module.newContent(
      portal_type='Subscription Request',
      title='TESTSUBREQ-%s' % self.generateNewId(),
      destination_decision_value=person,
      destination_project_value=self.project
    )
    subscription_request.submit()
    self.tic()
    self.login(person.getUserId())

    # Uses customer_relation='destination_decision'
    self.assertFalse(subscription_request.Base_hasSlapOSAccountingUserGroup())
    self.assertFalse(subscription_request.Base_hasSlapOSAccountingUserGroup(
      seller=True))
    self.assertTrue(subscription_request.Base_hasSlapOSAccountingUserGroup(
      customer=True))
    self.assertFalse(subscription_request.Base_hasSlapOSAccountingUserGroup(
      accountant=True))

  def test_Base_hasSlapOSAccountingUserGroup_sale_manager(self):
    # Assignment for customer is added automatically
    person = self.makePerson(self.project, user=1)
    self.addSaleManagerAssignment(person)
    self.tic()

    subscription_request = self.portal.subscription_request_module.newContent(
      portal_type='Subscription Request',
      title='TESTSUBREQ-%s' % self.generateNewId(),
      destination_decision_value=person,
      destination_project_value=self.project
    )
    subscription_request.submit()
    self.tic()
    self.login(person.getUserId())

    # Uses customer_relation='destination_decision'
    self.assertFalse(subscription_request.Base_hasSlapOSAccountingUserGroup())
    self.assertTrue(subscription_request.Base_hasSlapOSAccountingUserGroup(
      seller=True))
    self.assertTrue(subscription_request.Base_hasSlapOSAccountingUserGroup(
      customer=True))
    self.assertFalse(subscription_request.Base_hasSlapOSAccountingUserGroup(
      accountant=True))

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
