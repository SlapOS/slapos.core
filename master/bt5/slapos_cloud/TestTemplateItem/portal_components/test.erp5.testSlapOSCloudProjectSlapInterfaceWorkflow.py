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
from zExceptions import Unauthorized
import transaction

class TestSlapOSCoreProjectSlapInterfaceWorkflow(SlapOSTestCaseMixin):

  def afterSetUp(self):
    SlapOSTestCaseMixin.afterSetUp(self)
    self.project = self.addProject()

    person_user = self.makePerson(self.project)
    self.tic()

    # Login as new user
    self.login(person_user.getUserId())

    new_person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()
    self.assertEqual(person_user.getRelativeUrl(), new_person.getRelativeUrl())

    # Value set by the init
    self.assertTrue(self.project.getReference().startswith("PROJ-"),
      "Reference don't start with PROJ- : %s" % self.project.getReference())
    self.tic()

  def beforeTearDown(self):
    transaction.abort()

    
  def test_project_leaveProject_no_user(self):
    self.login()
    self.assertRaises(Unauthorized, self.project.leaveProject)

    
  def test_project_leaveProject_after_join(self):

    person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()

    self.logout()
    self.login(person.getUserId())

    assignment_list = [i for i in person.objectValues(portal_type="Assignment") 
                        if i.getDestinationProjectValue() == self.project]
    self.assertEqual(len(assignment_list), 1)
    self.assertEqual(assignment_list[0].getValidationState(), 'open')

    self.project.leaveProject()
    self.tic()

    self.login()
    assignment_list = [i for i in person.objectValues(portal_type="Assignment") 
                        if i.getDestinationProjectValue() == self.project]
    self.assertEqual(len(assignment_list), 1)
    self.assertEqual(assignment_list[0].getValidationState(), 'closed')

  def test_project_acceptInvitation_no_invitation_token(self):
    self.assertRaises(TypeError, self.project.acceptInvitation)

  def test_project_acceptInvitation_no_token_dont_exist(self):
    self.assertRaises(ValueError, self.project.acceptInvitation,
      invitation_token="DONOTEXIST")

  def test_project_acceptInvitation(self):
    person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()

    self.login()
    token = self.portal.invitation_token_module.newContent(
      portal_type="Invitation Token"
    )
    token_id = token.getId()

    # User is None
    self.assertRaises(ValueError, self.project.acceptInvitation,
      invitation_token=token_id)

    # Not validated yet
    self.login(person.getUserId())
    self.assertRaises(ValueError, self.project.acceptInvitation,
      invitation_token=token_id)

    self.login()
    token.validate()
    token.setSourceValue(person)
    self.login(person.getUserId())
    
    # Not used by the owner
    self.assertRaises(ValueError, self.project.acceptInvitation,
      invitation_token=token_id)


    self.login()
    token.setSourceValue(None)
    self.login(person.getUserId())
    self.project.acceptInvitation(invitation_token=token_id)

    self.tic()
    self.login()
    assignment_list = [i for i in person.objectValues(portal_type="Assignment") 
                        if i.getDestinationProjectValue() == self.project]
    self.assertEqual(len(assignment_list), 1)
    self.assertEqual(assignment_list[0].getValidationState(), 'open')

    self.assertEqual(token.getValidationState(), "invalidated")


  def test_project_acceptInvitation_already_member(self):
    person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()
    self.login()
    assignment_list = [i for i in person.objectValues(portal_type="Assignment") 
                        if i.getDestinationProjectValue() == self.project]
    self.assertEqual(len(assignment_list), 1)
    self.assertEqual(assignment_list[0].getValidationState(), 'open')

    token = self.portal.invitation_token_module.newContent(
      portal_type="Invitation Token"
    )
    token_id = token.getId()

    # User is None
    self.assertRaises(ValueError, self.project.acceptInvitation,
      invitation_token=token_id)

    # Not validated yet
    self.login(person.getUserId())
    self.assertRaises(ValueError, self.project.acceptInvitation,
      invitation_token=token_id)

    self.login()
    token.validate()
    token.setSourceValue(person)
    self.login(person.getUserId())
    
    # Not used by the owner
    self.assertRaises(ValueError, self.project.acceptInvitation,
      invitation_token=token_id)

    self.login()
    token.setSourceValue(None)
    self.login(person.getUserId())
    self.project.acceptInvitation(invitation_token=token_id)

    self.tic()
    self.login()
    assignment_list = [i for i in person.objectValues(portal_type="Assignment") 
                        if i.getDestinationProjectValue() == self.project]
    self.assertEqual(len(assignment_list), 1)
    self.assertEqual(assignment_list[0].getValidationState(), 'open')

    self.assertEqual(token.getValidationState(), "invalidated")
