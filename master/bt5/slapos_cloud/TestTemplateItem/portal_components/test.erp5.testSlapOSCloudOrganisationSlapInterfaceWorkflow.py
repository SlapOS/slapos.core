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

class TestSlapOSCoreOrganisationSlapInterfaceWorkflow(SlapOSTestCaseMixin):

  def afterSetUp(self):
    SlapOSTestCaseMixin.afterSetUp(self)
    portal = self.getPortalObject()
    
    person_user = self.makePerson()
    self.tic()

    # Login as new user
    self.login(person_user.getUserId())

    new_person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()
    self.assertEqual(person_user.getRelativeUrl(), new_person.getRelativeUrl())

    self.organisation = portal.organisation_module.newContent(
      portal_type="Organisation"
    )
    self.tic()

  def beforeTearDown(self):
    transaction.abort()

  def test_organisation_approveRegistration_with_reference(self):
    reference = "TEST-%s" % self.generateNewId()
    self.organisation.setReference(reference)
    self.organisation.approveRegistration()
    self.assertEqual(self.organisation.getReference(), reference)

  def test_organisation_approveRegistration_already_validated(self):

    # Login as admin since user cannot re-approve a validated organisation
    self.login()
    self.organisation.setReference(None)
    self.organisation.validate()
    # Don't raise if organisation is validated
    self.assertEqual(self.organisation.approveRegistration(), None)

  def test_organisation_approveRegistration_site(self, role="host", expected_prefix="SITE-"):
    person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()
    self.organisation.edit(role=role)
    self.organisation.approveRegistration()
    self.tic()

    self.logout()
    self.login(person.getUserId())

    self.assertEqual(self.organisation.getValidationState(),
      'validated')

    self.assertTrue(self.organisation.getReference().startswith(expected_prefix),
      "Reference don't start with %s : %s " % (
         expected_prefix, self.organisation.getReference()))

    assignment_list = [i for i in person.objectValues(portal_type="Assignment") 
                        if i.getDestinationValue() == self.organisation]
    self.assertEqual(len(assignment_list), 1)
    self.assertEqual(assignment_list[0].getValidationState(), 'open')
    self.assertIn("Assigment for Organisation ", assignment_list[0].getTitle())


  def test_organisation_approveRegistration_organisation(self):
    self.test_organisation_approveRegistration_site(role="client", expected_prefix="O-")

  def test_organisation_leaveOrganisation_no_user(self):
    self.login()
    self.assertRaises(Unauthorized, self.organisation.leaveOrganisation)
    
  def test_organisation_leaveOrganisation_after_join(self):

    person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()

    # Just make things fast, by using the API tested above
    self.organisation.approveRegistration()
    self.tic()

    self.logout()
    self.login(person.getUserId())

    assignment_list = [i for i in person.objectValues(portal_type="Assignment") 
                        if i.getDestinationValue() == self.organisation]
    self.assertEqual(len(assignment_list), 1)
    self.assertEqual(assignment_list[0].getValidationState(), 'open')

    self.organisation.leaveOrganisation()
    self.tic()

    self.login()
    assignment_list = [i for i in person.objectValues(portal_type="Assignment") 
                        if i.getDestinationValue() == self.organisation]
    self.assertEqual(len(assignment_list), 1)
    self.assertEqual(assignment_list[0].getValidationState(), 'closed')

  def test_organisation_acceptInvitation_no_invitation_token(self):
    self.assertRaises(TypeError, self.organisation.acceptInvitation)

  def test_organisation_acceptInvitation_no_token_dont_exist(self):
    self.assertRaises(ValueError, self.organisation.acceptInvitation,
      invitation_token="DONOTEXIST")

  def test_organisation_acceptInvitation(self):
    person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()

    self.login()
    token = self.portal.invitation_token_module.newContent(
      portal_type="Invitation Token"
    )
    token_id = token.getId()

    # User is None
    self.assertRaises(ValueError, self.organisation.acceptInvitation,
      invitation_token=token_id)

    # Not validated yet
    self.login(person.getUserId())
    self.assertRaises(ValueError, self.organisation.acceptInvitation,
      invitation_token=token_id)

    self.login()
    token.validate()
    token.setSourceValue(person)
    self.login(person.getUserId())
    
    # Not used by the owner
    self.assertRaises(ValueError, self.organisation.acceptInvitation,
      invitation_token=token_id)


    self.login()
    token.setSourceValue(None)
    self.login(person.getUserId())
    self.organisation.acceptInvitation(invitation_token=token_id)

    self.tic()
    self.login()
    assignment_list = [i for i in person.objectValues(portal_type="Assignment") 
                        if i.getDestinationValue() == self.organisation]
    self.assertEqual(len(assignment_list), 1)
    self.assertEqual(assignment_list[0].getValidationState(), 'open')

    self.assertEqual(token.getValidationState(), "invalidated")


  def test_organisation_acceptInvitation_already_member(self):
    person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()
    self.organisation.approveRegistration()
    self.tic()
    self.login()
    assignment_list = [i for i in person.objectValues(portal_type="Assignment") 
                        if i.getDestinationValue() == self.organisation]
    self.assertEqual(len(assignment_list), 1)
    self.assertEqual(assignment_list[0].getValidationState(), 'open')

    token = self.portal.invitation_token_module.newContent(
      portal_type="Invitation Token"
    )
    token_id = token.getId()

    # User is None
    self.assertRaises(ValueError, self.organisation.acceptInvitation,
      invitation_token=token_id)

    # Not validated yet
    self.login(person.getUserId())
    self.assertRaises(ValueError, self.organisation.acceptInvitation,
      invitation_token=token_id)

    self.login()
    token.validate()
    token.setSourceValue(person)
    self.login(person.getUserId())
    
    # Not used by the owner
    self.assertRaises(ValueError, self.organisation.acceptInvitation,
      invitation_token=token_id)

    self.login()
    token.setSourceValue(None)
    self.login(person.getUserId())
    self.organisation.acceptInvitation(invitation_token=token_id)

    self.tic()
    self.login()
    assignment_list = [i for i in person.objectValues(portal_type="Assignment") 
                        if i.getDestinationValue() == self.organisation]
    self.assertEqual(len(assignment_list), 1)
    self.assertEqual(assignment_list[0].getValidationState(), 'open')

    self.assertEqual(token.getValidationState(), "invalidated")
