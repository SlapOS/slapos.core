# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2002-2012 Nexedi SA and Contributors. All Rights Reserved.
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################
from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixin
import transaction
from AccessControl.SecurityManagement import getSecurityManager, \
             setSecurityManager


class TestSlapOSCorePersonRequestComputeNode(SlapOSTestCaseMixin):

  def generateNewComputeNodeTitle(self):
    return 'My Comp %s' % self.generateNewId()

  def afterSetUp(self):
    SlapOSTestCaseMixin.afterSetUp(self)
    self.project = self.addProject()
    person_user = self.makePerson(self.project)
    # Only admin can create computer node
    self.addProjectProductionManagerAssignment(person_user, self.project)
    self.tic()

    # Login as new user
    self.login(person_user.getUserId())
    new_person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()
    self.assertEqual(person_user.getRelativeUrl(), new_person.getRelativeUrl())

  def beforeTearDown(self):
    pass

  def test_requestComputeNode_requiredParameter(self):
    person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()

    # compute_node_title is mandatory
    self.assertRaises(TypeError, person.requestComputeNode,
                      project_reference=self.project.getReference())

    compute_node_title = self.generateNewComputeNodeTitle()

    # project_reference is mandatory
    self.assertRaises(TypeError, person.requestComputeNode,
                      compute_node_title=compute_node_title)

    # if provided does not raise
    person.requestComputeNode(project_reference=self.project.getReference(),
                              compute_node_title=compute_node_title)

  def test_requestComputeNode_request(self):
    person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()

    compute_node_title = self.generateNewComputeNodeTitle()
    person.requestComputeNode(project_reference=self.project.getReference(),
                              compute_node_title=compute_node_title)

    # check what is returned via request
    compute_node_url = person.REQUEST.get('compute_node')
    compute_node_absolute_url = person.REQUEST.get('compute_node_url')
    compute_node_reference = person.REQUEST.get('compute_node_reference')

    self.assertNotEqual(None, compute_node_url)
    self.assertNotEqual(None, compute_node_absolute_url)
    self.assertNotEqual(None, compute_node_reference)

  def test_requestComputeNode_createdComputeNode(self):
    person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()

    compute_node_title = self.generateNewComputeNodeTitle()
    person.requestComputeNode(project_reference=self.project.getReference(),
                              compute_node_title=compute_node_title)

    # check what is returned via request
    compute_node_url = person.REQUEST.get('compute_node')
    compute_node_absolute_url = person.REQUEST.get('compute_node_url')
    compute_node_reference = person.REQUEST.get('compute_node_reference')

    self.assertNotEqual(None, compute_node_url)
    self.assertNotEqual(None, compute_node_absolute_url)
    self.assertNotEqual(None, compute_node_reference)

    # check that title is ok
    compute_node = person.restrictedTraverse(compute_node_url)
    self.assertEqual(compute_node_title, compute_node.getTitle())

    # check that data are sane
    self.assertEqual(compute_node_absolute_url, compute_node.absolute_url())
    self.assertEqual(compute_node_reference, compute_node.getReference())
    self.assertEqual('COMP-%s' % compute_node.getId(), compute_node.getReference())
    self.assertEqual('validated', compute_node.getValidationState())
    self.assertEqual('open', compute_node.getAllocationScope())
    self.assertEqual('close', compute_node.getCapacityScope())

  def test_requestComputeNode_notReindexedCompute(self):
    person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()

    compute_node_title = self.generateNewComputeNodeTitle()
    person.requestComputeNode(project_reference=self.project.getReference(),
                              compute_node_title=compute_node_title)
    transaction.commit()
    self.assertRaises(NotImplementedError, person.requestComputeNode,
                      project_reference=self.project.getReference(),
                      compute_node_title=compute_node_title)

  def test_requestComputeNode_multiple_request_createdComputeNode(self):
    person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()

    compute_node_title = self.generateNewComputeNodeTitle()
    compute_node_title2 = self.generateNewComputeNodeTitle()
    person.requestComputeNode(project_reference=self.project.getReference(),
                              compute_node_title=compute_node_title)

    # check what is returned via request
    compute_node_url = person.REQUEST.get('compute_node')
    compute_node_absolute_url = person.REQUEST.get('compute_node_url')
    compute_node_reference = person.REQUEST.get('compute_node_reference')

    self.assertNotEqual(None, compute_node_url)
    self.assertNotEqual(None, compute_node_absolute_url)
    self.assertNotEqual(None, compute_node_reference)

    # check that title is ok
    compute_node = person.restrictedTraverse(compute_node_url)
    self.assertEqual(compute_node_title, compute_node.getTitle())

    # check that data are sane
    self.assertEqual(compute_node_absolute_url, compute_node.absolute_url())
    self.assertEqual(compute_node_reference, compute_node.getReference())
    self.assertEqual('COMP-%s' % compute_node.getId(), compute_node.getReference())
    self.assertEqual('validated', compute_node.getValidationState())
    self.assertEqual('open', compute_node.getAllocationScope())
    self.assertEqual('close', compute_node.getCapacityScope())

    self.tic()

    # request again the same compute_node
    person.requestComputeNode(project_reference=self.project.getReference(),
                              compute_node_title=compute_node_title)

    # check what is returned via request
    compute_node_url = person.REQUEST.get('compute_node')
    compute_node_absolute_url = person.REQUEST.get('compute_node_url')
    compute_node_reference = person.REQUEST.get('compute_node_reference')

    self.assertNotEqual(None, compute_node_url)
    self.assertNotEqual(None, compute_node_absolute_url)
    self.assertNotEqual(None, compute_node_reference)

    # check that title is ok
    compute_node = person.restrictedTraverse(compute_node_url)
    self.assertEqual(compute_node_title, compute_node.getTitle())

    # check that data are sane
    self.assertEqual(compute_node_absolute_url, compute_node.absolute_url())
    self.assertEqual(compute_node_reference, compute_node.getReference())
    self.assertEqual('COMP-%s' % compute_node.getId(), compute_node.getReference())
    self.assertEqual('validated', compute_node.getValidationState())
    self.assertEqual('open', compute_node.getAllocationScope())
    self.assertEqual('close', compute_node.getCapacityScope())

    # and now another one
    person.requestComputeNode(project_reference=self.project.getReference(),
                              compute_node_title=compute_node_title2)

    # check what is returned via request
    compute_node_url2 = person.REQUEST.get('compute_node')
    compute_node_absolute_url2 = person.REQUEST.get('compute_node_url')
    compute_node_reference2 = person.REQUEST.get('compute_node_reference')

    self.assertNotEqual(None, compute_node_url2)
    self.assertNotEqual(None, compute_node_absolute_url2)
    self.assertNotEqual(None, compute_node_reference2)

    # check that compute_nodes are really different objects
    self.assertNotEqual(compute_node_url2, compute_node_url)

    # check that title is ok
    compute_node2 = person.restrictedTraverse(compute_node_url2)
    self.assertEqual(compute_node_title2, compute_node2.getTitle())

    # check that data are sane
    self.assertEqual(compute_node_absolute_url2, compute_node2.absolute_url())
    self.assertEqual(compute_node_reference2, compute_node2.getReference())
    self.assertEqual('COMP-%s' % compute_node2.getId(), compute_node2.getReference())
    self.assertEqual('validated', compute_node2.getValidationState())
    self.assertEqual('open', compute_node2.getAllocationScope())
    self.assertEqual('close', compute_node2.getCapacityScope())

  def test_requestComputeNode_duplicatedComputeNode(self):
    person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()

    compute_node_title = self.generateNewComputeNodeTitle()
    person.requestComputeNode(project_reference=self.project.getReference(),
                              compute_node_title=compute_node_title)

    # check what is returned via request
    compute_node_url = person.REQUEST.get('compute_node')
    compute_node_absolute_url = person.REQUEST.get('compute_node_url')
    compute_node_reference = person.REQUEST.get('compute_node_reference')

    self.assertNotEqual(None, compute_node_url)
    self.assertNotEqual(None, compute_node_absolute_url)
    self.assertNotEqual(None, compute_node_reference)

    # check that title is ok
    compute_node = person.restrictedTraverse(compute_node_url)

    sm = getSecurityManager()
    try:
      self.login()
      compute_node2 = compute_node.Base_createCloneDocument(batch_mode=1)
      compute_node2.validate()
    finally:
      setSecurityManager(sm)
    self.tic()

    self.assertRaises(NotImplementedError, person.requestComputeNode,
                      project_reference=self.project.getReference(),
                      compute_node_title=compute_node_title)


class TestSlapOSCorePersonRequestNetwork(SlapOSTestCaseMixin):

  def generateNewNetworkTitle(self):
    return 'My Network %s' % self.generateNewId()

  def afterSetUp(self):
    SlapOSTestCaseMixin.afterSetUp(self)
    self.project = self.addProject()
    person_user = self.makePerson(self.project)
    # Only admin can create computer network
    self.addProjectProductionManagerAssignment(person_user, self.project)
    self.tic()

    # Login as new user
    self.login(person_user.getUserId())
    new_person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()
    self.assertEqual(person_user.getRelativeUrl(), new_person.getRelativeUrl())

  def beforeTearDown(self):
    pass

  def test_Person_requestNetwork_title_is_mandatory(self):
    person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()
    self.assertRaises(TypeError, person.requestNetwork,
                      project_reference=self.project.getReference())

  def test_Person_requestNetwork_project_is_mandatory(self):
    person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()
    self.assertRaises(TypeError, person.requestNetwork,
                      network_title=self.generateNewNetworkTitle())

  def test_Person_requestNetwork(self):
    person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()
    network_title = self.generateNewNetworkTitle()
    person.requestNetwork(network_title=network_title,
                          project_reference=self.project.getReference())

    self.tic()
    self.login()
    # check what is returned via request
    network_relative_url = person.REQUEST.get('computer_network_relative_url')

    self.assertNotEqual(None, network_relative_url)

    network = person.restrictedTraverse(network_relative_url)
    self.assertEqual(network.getFollowUp(),
                     self.project.getRelativeUrl())
    self.assertEqual(network.getTitle(), network_title)
    self.assertEqual(network.getValidationState(), "validated")
    self.assertIn("NET-", network.getReference())


  def test_Person_requestNetwork_duplicated(self):
    person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()
    network_title = self.generateNewNetworkTitle()
    person.requestNetwork(network_title=network_title,
                          project_reference=self.project.getReference())
    self.tic()
    self.login()

    # check what is returned via request
    network_relative_url = person.REQUEST.get('computer_network_relative_url')

    self.assertNotEqual(None, network_relative_url)

    network = person.restrictedTraverse(network_relative_url)
    self.assertEqual(network.getFollowUp(),
                     self.project.getRelativeUrl())
    self.assertEqual(network.getTitle(), network_title)
    self.assertEqual(network.getValidationState(), "validated")
    self.assertIn("NET-", network.getReference())

    network2 = network.Base_createCloneDocument(batch_mode=1)
    network2.validate()
    self.tic()

    self.login(person.getUserId())
    self.assertRaises(NotImplementedError, person.requestNetwork,
                      network_title=network_title,
                      project_reference=self.project.getReference())

  def test_Person_requestNetwork_request_again(self):
    person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()
    network_title = self.generateNewNetworkTitle()
    person.requestNetwork(network_title=network_title,
                          project_reference=self.project.getReference())

    # check what is returned via request
    network_relative_url = person.REQUEST.get('computer_network_relative_url')

    self.assertNotEqual(None, network_relative_url)

    self.tic()
    self.login()
    # check what is returned via request
    person.REQUEST.set('computer_network_relative_url', None)

    self.login(person.getUserId())
    person.requestNetwork(network_title=network_title,
                          project_reference=self.project.getReference())

    # check what is returned via request
    same_network_relative_url = person.REQUEST.get('computer_network_relative_url')
    self.assertEqual(same_network_relative_url, network_relative_url)


class TestSlapOSCorePersonRequestToken(SlapOSTestCaseMixin):

  def generateNewTokenUrl(self):
    return 'https://%s.no.where/%s' % (
      self.generateNewId(),
      self.generateNewId())

  def afterSetUp(self):
    SlapOSTestCaseMixin.afterSetUp(self)
    self.project = self.addProject()
    person_user = self.makePerson(self.project)
    self.addProjectProductionManagerAssignment(person_user, self.project)
    self.tic()

    # Login as new user
    self.login(person_user.getUserId())
    new_person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()
    self.assertEqual(person_user.getRelativeUrl(), new_person.getRelativeUrl())

  def beforeTearDown(self):
    pass
  
  def test_Person_requestToken_requested_url_is_mandatory(self):
    person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()
    self.assertRaises(TypeError, person.requestToken)

  def test_Person_requestToken(self):
    person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()
    request_url = self.generateNewTokenUrl()
    person.requestToken(request_url=request_url)

    self.tic()
    self.login()
    # check what is returned via request
    token_id = person.REQUEST.get('token')

    self.assertNotEqual(None, token_id)
    
    token = self.portal.access_token_module[token_id]
    self.assertEqual(token.getAgent(),
                    person.getRelativeUrl())
    self.assertEqual(token.getUrlString(), request_url)
    self.assertEqual(token.getValidationState(), "validated")
    self.assertEqual(
      token.getPortalType(), "One Time Restricted Access Token")
    self.assertEqual(token.getUrlMethod(), "POST")

