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

class TestSlapOSCoreNetworkSlapInterfaceWorkflow(SlapOSTestCaseMixin):

  def afterSetUp(self):
    SlapOSTestCaseMixin.afterSetUp(self)
    portal = self.getPortalObject()
    self.project = self.addProject()

    person_user = self.makePerson(self.project)
    self.addProjectProductionManagerAssignment(person_user, self.project)
    self.tic()

    # Login as new user
    self.login(person_user.getUserId())

    new_person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()
    self.assertEqual(person_user.getRelativeUrl(), new_person.getRelativeUrl())

    self.network = portal.computer_network_module.newContent(
      portal_type="Computer Network",
      follow_up_value=self.project
    )
    self.tic()
    self.assertEqual(
      self.network.getReference(), None)

  def beforeTearDown(self):
    transaction.abort()

  def test_network_approveRegistration_with_reference(self):
    reference = "TEST-%s" % self.generateNewId()
    self.network.setReference(reference)
    self.network.approveRegistration()
    self.assertEqual(self.network.getReference(), reference)

  def test_organisation_approveRegistration_already_validated(self):

    # Login as admin since user cannot re-approve a validated organisation
    self.login()
    self.network.setReference(None)
    self.network.validate()
    # Don't raise if network is validated
    self.assertEqual(self.network.approveRegistration(), None)
