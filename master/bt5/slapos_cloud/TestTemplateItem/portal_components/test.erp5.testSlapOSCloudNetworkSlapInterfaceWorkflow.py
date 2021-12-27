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
from time import sleep
from zExceptions import Unauthorized
import transaction

class TestSlapOSCoreNetworkSlapInterfaceWorkflow(SlapOSTestCaseMixin):

  def afterSetUp(self):
    SlapOSTestCaseMixin.afterSetUp(self)
    portal = self.getPortalObject()
    
    person_user = self.makePerson()
    self.tic()

    # Login as new user
    self.login(person_user.getUserId())

    new_person = self.portal.portal_membership.getAuthenticatedMember().getUserValue()
    self.assertEqual(person_user.getRelativeUrl(), new_person.getRelativeUrl())

    self.network = portal.computer_network_module.newContent(
      portal_type="Computer Network"
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

  def _makeProject(self):
    project = self.portal.project_module.newContent()
    project.edit(reference="TESTPROJ-%s" % project.getId())
    project.validate()

    self.tic()
    return project

  def _makeOrganisation(self):
    organisation = self.portal.organisation_module.newContent()
    organisation.edit(reference="TESTSITE-%s" % organisation.getId())
    organisation.validate()

    self.tic()
    return organisation

  def test_ComputerNetwork_requestTransfer_project(self):
    source_administrator = self.portal.portal_membership.getAuthenticatedMember().getUserValue()
    self.network.setSourceAdministrationValue(source_administrator)

    self.login()
    self.network.approveRegistration()

    project = self._makeProject()
    other_project = self._makeProject()
    self.tic()

    self.login(source_administrator.getUserId())

    self.assertEqual(self.network.Item_getCurrentProjectValue(), None)
    self.assertEqual(self.network.Item_getCurrentOwnerValue(), None)

    # Place in a project    
    self.network.requestTransfer(
      destination_section=None,
      destination_project=project.getRelativeUrl())

    self.tic()
    
    self.assertEqual(self.network.Item_getCurrentProjectValue(), project)
    self.assertEqual(self.network.Item_getCurrentOwnerValue(), source_administrator)
    
    self.assertEqual(1,
      len(self.network.getAggregateRelatedList(portal_type="Internal Packing List Line"))
    )
    self.login(source_administrator.getUserId())

    # We don't remove from Project if destination project is not provided
    self.network.requestTransfer(
      destination_project=None,
      destination_section=None
    )
    self.tic()

    self.assertEqual(self.network.Item_getCurrentProjectValue(), project)
    self.assertEqual(self.network.Item_getCurrentOwnerValue(), source_administrator)
    self.assertEqual(2,
      len(self.network.getAggregateRelatedList(portal_type="Internal Packing List Line"))
    )

    # Ensure that we don't have 2 new Internal Packing lists in the same second 
    sleep(1)
    # Place in another project    
    self.network.requestTransfer(
      destination_section=None,
      destination_project=other_project.getRelativeUrl())

    self.tic()
    
    self.assertEqual(self.network.Item_getCurrentProjectValue(), other_project)
    self.assertEqual(self.network.Item_getCurrentOwnerValue(), source_administrator)
    
    self.assertEqual(3,
      len(self.network.getAggregateRelatedList(portal_type="Internal Packing List Line"))
    )
    self.login(source_administrator.getUserId())

    # Ensure that we don't have 2 new Internal Packing lists in the same second 
    sleep(1)
    # We don't remove from Project if destination project is not provided
    self.network.requestTransfer(
      destination_project=None,
      destination_section=None
    )
    self.tic()

    self.assertEqual(self.network.Item_getCurrentProjectValue(), other_project)
    self.assertEqual(self.network.Item_getCurrentOwnerValue(), source_administrator)
    self.assertEqual(4,
      len(self.network.getAggregateRelatedList(portal_type="Internal Packing List Line"))
    )

  def test_ComputerNetwork_requestTransfer_owner(self):
    source_administrator = self.portal.portal_membership.getAuthenticatedMember().getUserValue()
    self.network.setSourceAdministrationValue(source_administrator)

    self.login()
    self.network.approveRegistration()
    organisation = self._makeOrganisation()
    other_organisation = self._makeOrganisation()
    self.tic()

    self.login(source_administrator.getUserId())

    self.assertEqual(self.network.Item_getCurrentProjectValue(), None)
    self.assertEqual(self.network.Item_getCurrentOwnerValue(), None)

    self.network.requestTransfer(
      destination_project=None,
      destination_section=organisation.getRelativeUrl())

    self.tic()
    
    self.assertEqual(self.network.Item_getCurrentProjectValue(), None)
    self.assertEqual(self.network.Item_getCurrentOwnerValue(), organisation)
    
    self.assertEqual(1,
      len(self.network.getAggregateRelatedList(portal_type="Internal Packing List Line"))
    )
    self.login(source_administrator.getUserId())

    # Ensure that we don't have 2 new Internal Packing lists in the same second 
    sleep(1)
    # We don't remove from Project if destination project is not provided
    self.network.requestTransfer(
      destination_project=None,
      destination_section=None)
    self.tic()

    self.assertEqual(self.network.Item_getCurrentProjectValue(), None)
    self.assertEqual(self.network.Item_getCurrentOwnerValue(), organisation)

    # Ensure that we don't have 2 new Internal Packing lists in the same second 
    sleep(1)
    # Place in another project    
    self.network.requestTransfer(
      destination_project=None,
      destination_section=other_organisation.getRelativeUrl())

    self.tic()
        
    self.assertEqual(3,
      len(self.network.getAggregateRelatedList(portal_type="Internal Packing List Line"))
    )
    self.assertEqual(self.network.Item_getCurrentProjectValue(), None)
    self.assertEqual(self.network.Item_getCurrentOwnerValue(), other_organisation)
    
    self.assertEqual(3,
      len(self.network.getAggregateRelatedList(portal_type="Internal Packing List Line"))
    )
    self.login(source_administrator.getUserId())

    # Ensure that we don't have 2 new Internal Packing lists in the same second 
    sleep(1)
    # We don't remove from Project if destination project is not provided
    self.network.requestTransfer(
      destination_project=None,
      destination_section=None
    )
    self.tic()

    self.assertEqual(self.network.Item_getCurrentProjectValue(), None)
    self.assertEqual(self.network.Item_getCurrentOwnerValue(), other_organisation)
    self.assertEqual(4,
      len(self.network.getAggregateRelatedList(portal_type="Internal Packing List Line"))
    )


  def test_ComputerNetwork_requestTransfer_Unauthorized(self):    
    self.network.approveRegistration()
    self.login()
    self.assertRaises(Unauthorized, self.network.requestTransfer)

    source_administrator = self.makePerson(user=1)
    self.assertEqual(1 , len(source_administrator.objectValues( portal_type="ERP5 Login")))

    self.login(source_administrator.getUserId())
    self.assertRaises(Unauthorized, self.network.requestTransfer)

    self.login()
    other_user = self.makePerson(user=1)
    self.assertEqual(1 , len(other_user.objectValues(portal_type="ERP5 Login")))

    self.network.setSourceAdministrationValue(source_administrator)
    self.tic()

    self.assertRaises(Unauthorized, self.network.requestTransfer)
    self.login(other_user.getUserId())
    self.assertRaises(Unauthorized, self.network.requestTransfer)

    self.login(source_administrator.getUserId())
    self.network.requestTransfer(
      destination_project=None,
      destination_section=None
    )

