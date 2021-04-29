# -*- coding:utf-8 -*-
##############################################################################
#
# Copyright (c) 2021 Nexedi SA and Contributors. All Rights Reserved.
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA
#
##############################################################################

from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixin
from time import sleep

from zExceptions import Unauthorized

class TestComputerNetworkcreateMovement(SlapOSTestCaseMixin):

  def _makeProject(self):
    project = self.portal.project_module.newContent()
    project.edit(reference="TESTPROJ-%s" % project.getId())
    project.validate()

    self.tic()
    return project

  def _makeComputerNetwork(self):
    network = self.portal.computer_network_module.newContent()
    network.edit(reference="TESTNET-%s" % network.getId())
    network.validate()
    self.tic()
    return network

  def _makeOrganisation(self):
    organisation = self.portal.organisation_module.newContent()
    organisation.edit(reference="TESTSITE-%s" % organisation.getId())
    organisation.validate()

    self.tic()
    return organisation

  def test_project(self):
    network = self._makeComputerNetwork()
    source_administrator = self.makePerson(user=1)
    network.setSourceAdministrationValue(source_administrator)
    project = self._makeProject()
    other_project = self._makeProject()
    self.tic()

    self.login(source_administrator.getUserId())

    self.assertEqual(network.Item_getCurrentProjectValue(), None)
    self.assertEqual(network.Item_getCurrentOwnerValue(), None)

    # Place in a project    
    self.assertEqual(network.ComputerNetwork_createMovement(
      destination_project=project.getRelativeUrl()), None)

    self.tic()
    
    self.assertEqual(network.Item_getCurrentProjectValue(), project)
    self.assertEqual(network.Item_getCurrentOwnerValue(), source_administrator)
    
    self.assertEqual(1,
      len(network.getAggregateRelatedList(portal_type="Internal Packing List Line"))
    )
    self.login(source_administrator.getUserId())

    # We don't remove from Project if destination project is not provided
    self.assertEqual(network.ComputerNetwork_createMovement(), None)
    self.tic()

    self.assertEqual(network.Item_getCurrentProjectValue(), project)
    self.assertEqual(network.Item_getCurrentOwnerValue(), source_administrator)
    self.assertEqual(2,
      len(network.getAggregateRelatedList(portal_type="Internal Packing List Line"))
    )

    # Place in another project    
    self.assertEqual(network.ComputerNetwork_createMovement(
      destination_project=other_project.getRelativeUrl()), None)

    self.tic()
    
    self.assertEqual(network.Item_getCurrentProjectValue(), other_project)
    self.assertEqual(network.Item_getCurrentOwnerValue(), source_administrator)
    
    self.assertEqual(3,
      len(network.getAggregateRelatedList(portal_type="Internal Packing List Line"))
    )
    self.login(source_administrator.getUserId())

    # We don't remove from Project if destination project is not provided
    self.assertEqual(network.ComputerNetwork_createMovement(), None)
    self.tic()

    self.assertEqual(network.Item_getCurrentProjectValue(), other_project)
    self.assertEqual(network.Item_getCurrentOwnerValue(), source_administrator)
    self.assertEqual(4,
      len(network.getAggregateRelatedList(portal_type="Internal Packing List Line"))
    )

  def test_owner(self):
    network = self._makeComputerNetwork()
    source_administrator = self.makePerson(user=1)
    network.setSourceAdministrationValue(source_administrator)
    organisation = self._makeOrganisation()
    other_organisation = self._makeOrganisation()
    self.tic()

    self.login(source_administrator.getUserId())

    self.assertEqual(network.Item_getCurrentProjectValue(), None)
    self.assertEqual(network.Item_getCurrentOwnerValue(), None)

    self.assertEqual(network.ComputerNetwork_createMovement(
      destination_section=organisation.getRelativeUrl()), None)

    self.tic()
    
    self.assertEqual(network.Item_getCurrentProjectValue(), None)
    self.assertEqual(network.Item_getCurrentOwnerValue(), organisation)
    
    self.assertEqual(1,
      len(network.getAggregateRelatedList(portal_type="Internal Packing List Line"))
    )
    self.login(source_administrator.getUserId())

    # We don't remove from Project if destination project is not provided
    self.assertEqual(network.ComputerNetwork_createMovement(), None)
    self.tic()

    self.assertEqual(network.Item_getCurrentProjectValue(), None)
    self.assertEqual(network.Item_getCurrentOwnerValue(), organisation)

    # Place in another project    
    self.assertEqual(network.ComputerNetwork_createMovement(
      destination_section=other_organisation.getRelativeUrl()), None)

    self.tic()
        
    self.assertEqual(3,
      len(network.getAggregateRelatedList(portal_type="Internal Packing List Line"))
    )
    self.assertEqual(network.Item_getCurrentProjectValue(), None)
    self.assertEqual(network.Item_getCurrentOwnerValue(), other_organisation)
    
    self.assertEqual(3,
      len(network.getAggregateRelatedList(portal_type="Internal Packing List Line"))
    )
    self.login(source_administrator.getUserId())

    # We don't remove from Project if destination project is not provided
    self.assertEqual(network.ComputerNetwork_createMovement(), None)
    self.tic()

    self.assertEqual(network.Item_getCurrentProjectValue(), None)
    self.assertEqual(network.Item_getCurrentOwnerValue(), other_organisation)
    self.assertEqual(4,
      len(network.getAggregateRelatedList(portal_type="Internal Packing List Line"))
    )


  def testUnauthorized(self):
    network = self._makeComputerNetwork()
    
    self.assertRaises(Unauthorized, network.ComputerNetwork_createMovement)

    source_administrator = self.makePerson(user=1)
    self.assertEqual(1 , len(source_administrator.objectValues( portal_type="ERP5 Login")))

    self.login(source_administrator.getUserId())
    self.assertRaises(Unauthorized, network.ComputerNetwork_createMovement)

    self.login()
    other_user = self.makePerson(user=1)
    self.assertEqual(1 , len(other_user.objectValues(portal_type="ERP5 Login")))

    network.setSourceAdministrationValue(source_administrator)
    self.tic()

    self.assertRaises(Unauthorized, network.ComputerNetwork_createMovement)
    self.login(other_user.getUserId())
    self.assertRaises(Unauthorized, network.ComputerNetwork_createMovement)

    self.login(source_administrator.getUserId())
    self.assertEqual(network.ComputerNetwork_createMovement(), None)


class TestComputercreateMovement(SlapOSTestCaseMixin):
  
  def _makeComputer(self, owner=None, allocation_scope='open/public'):
    computer = self.portal.computer_module\
        .template_computer.Base_createCloneDocument(batch_mode=1)
    computer.edit(reference="TESTCOMP-%s" % computer.getId())
    computer.validate()

    self.tic()
    return computer

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

  def testUnauthorized(self):
    computer = self._makeComputer()
    site = self._makeOrganisation()

    self.assertRaises(Unauthorized, computer.Computer_createMovement)

    source_administrator = self.makePerson(user=1)
    self.assertEqual(1 , len(source_administrator.objectValues( portal_type="ERP5 Login")))

    self.login(source_administrator.getUserId())
    self.assertRaises(Unauthorized, computer.Computer_createMovement)

    self.login()
    other_user = self.makePerson(user=1)
    self.assertEqual(1 , len(other_user.objectValues(portal_type="ERP5 Login")))

    computer.setSourceAdministrationValue(source_administrator)
    self.tic()

    self.assertRaises(Unauthorized, computer.Computer_createMovement)
    self.login(other_user.getUserId())
    self.assertRaises(Unauthorized, computer.Computer_createMovement)

    self.login(source_administrator.getUserId())
    self.assertEqual(computer.Computer_createMovement(destination=site.getRelativeUrl()), None)


  def test_project(self):
    computer = self._makeComputer()
    source_administrator = self.makePerson(user=1)
    computer.setSourceAdministrationValue(source_administrator)
    project = self._makeProject()
    other_project = self._makeProject()
    site = self._makeOrganisation()
    self.tic()

    self.login(source_administrator.getUserId())

    self.assertEqual(computer.Item_getCurrentProjectValue(), None)
    self.assertEqual(computer.Item_getCurrentOwnerValue(), None)
    self.assertEqual(computer.Item_getCurrentSiteValue(), None)

    # Place in a project    
    self.assertEqual(computer.Computer_createMovement(
      destination=site.getRelativeUrl(),
      destination_project=project.getRelativeUrl()), None)

    self.tic()
    
    self.assertEqual(computer.Item_getCurrentProjectValue(), project)
    self.assertEqual(computer.Item_getCurrentOwnerValue(), source_administrator)
    self.assertEqual(computer.Item_getCurrentSiteValue(), site)

    self.assertEqual(1,
      len(computer.getAggregateRelatedList(portal_type="Internal Packing List Line"))
    )

    # Ensure that we don't have 2 new Internal Packing lists in the same second 
    sleep(3)
    
    self.login(source_administrator.getUserId())

    # We don't remove from Project if destination project is not provided
    self.assertEqual(computer.Computer_createMovement(), None)
    self.tic()

    self.assertEqual(computer.Item_getCurrentProjectValue(), project)
    self.assertEqual(computer.Item_getCurrentOwnerValue(), source_administrator)
    self.assertEqual(2,
      len(computer.getAggregateRelatedList(portal_type="Internal Packing List Line"))
    )

    # Ensure that we don't have 2 new Internal Packing lists in the same second 
    sleep(3)
    
    # Place in another project    
    self.assertEqual(computer.Computer_createMovement(
      destination_project=other_project.getRelativeUrl()), None)

    self.tic()
    
    self.assertEqual(computer.Item_getCurrentProjectValue(), other_project)
    self.assertEqual(computer.Item_getCurrentOwnerValue(), source_administrator)
    self.assertEqual(computer.Item_getCurrentSiteValue(), site)

    self.assertEqual(3,
      len(computer.getAggregateRelatedList(portal_type="Internal Packing List Line"))
    )
    self.login(source_administrator.getUserId())

    # Ensure that we don't have 2 new Internal Packing lists in the same second 
    sleep(3)
    
    # We don't remove from Project if destination project is not provided
    self.assertEqual(computer.Computer_createMovement(), None)
    self.tic()

    self.assertEqual(computer.Item_getCurrentProjectValue(), other_project)
    self.assertEqual(computer.Item_getCurrentOwnerValue(), source_administrator)
    self.assertEqual(computer.Item_getCurrentSiteValue(), site)

    self.assertEqual(4,
      len(computer.getAggregateRelatedList(portal_type="Internal Packing List Line"))
    )

  def test_owner(self):
    computer = self._makeComputer()
    source_administrator = self.makePerson(user=1)
    computer.setSourceAdministrationValue(source_administrator)
    organisation = self._makeOrganisation()
    other_organisation = self._makeOrganisation()
    site = self._makeOrganisation()
    self.tic()

    self.login(source_administrator.getUserId())

    self.assertEqual(computer.Item_getCurrentProjectValue(), None)
    self.assertEqual(computer.Item_getCurrentOwnerValue(), None)

    self.assertEqual(computer.Computer_createMovement(
       destination=site.getRelativeUrl(),
       destination_section=organisation.getRelativeUrl()), None)

    self.tic()
    
    self.assertEqual(computer.Item_getCurrentProjectValue(), None)
    self.assertEqual(computer.Item_getCurrentOwnerValue(), organisation)
    self.assertEqual(computer.Item_getCurrentSiteValue(), site)

    self.assertEqual(1,
      len(computer.getAggregateRelatedList(portal_type="Internal Packing List Line"))
    )
    # Ensure that we don't have 2 new Internal Packing lists in the same second 
    sleep(3)
    self.login(source_administrator.getUserId())

    self.assertEqual(computer.Computer_createMovement(), None)
    self.tic()

    self.assertEqual(computer.Item_getCurrentProjectValue(), None)
    self.assertEqual(computer.Item_getCurrentOwnerValue(), source_administrator)
    self.assertEqual(computer.Item_getCurrentSiteValue(), site)

    # Ensure that we don't have 2 new Internal Packing lists in the same second 
    sleep(3)
    
    # Place in another project    
    self.assertEqual(computer.Computer_createMovement(
      destination_section=other_organisation.getRelativeUrl()), None)

    self.tic()
        
    self.assertEqual(3,
      len(computer.getAggregateRelatedList(portal_type="Internal Packing List Line"))
    )
    self.assertEqual(computer.Item_getCurrentProjectValue(), None)
    self.assertEqual(computer.Item_getCurrentOwnerValue(), other_organisation)
    self.assertEqual(computer.Item_getCurrentSiteValue(), site)

    self.assertEqual(3,
      len(computer.getAggregateRelatedList(portal_type="Internal Packing List Line"))
    )
    self.login(source_administrator.getUserId())

    # Ensure that we don't have 2 new Internal Packing lists in the same second 
    sleep(3)
    # We don't remove from Project if destination project is not provided
    self.assertEqual(computer.Computer_createMovement(), None)
    self.tic()

    self.assertEqual(computer.Item_getCurrentProjectValue(), None)
    self.assertEqual(computer.Item_getCurrentOwnerValue(), source_administrator)
    self.assertEqual(computer.Item_getCurrentSiteValue(), site)

    self.assertEqual(4,
      len(computer.getAggregateRelatedList(portal_type="Internal Packing List Line"))
    )

  def test_site(self):
    computer = self._makeComputer()
    source_administrator = self.makePerson(user=1)
    computer.setSourceAdministrationValue(source_administrator)
    site = self._makeOrganisation()
    other_site = self._makeOrganisation()

    self.tic()

    self.login(source_administrator.getUserId())

    self.assertEqual(computer.Item_getCurrentProjectValue(), None)
    self.assertEqual(computer.Item_getCurrentOwnerValue(), None)

    self.assertEqual(computer.Computer_createMovement(
       destination=site.getRelativeUrl()), None)

    self.tic()
    
    self.assertEqual(computer.Item_getCurrentProjectValue(), None)
    self.assertEqual(computer.Item_getCurrentOwnerValue(), source_administrator)
    self.assertEqual(computer.Item_getCurrentSiteValue(), site)

    self.assertEqual(1,
      len(computer.getAggregateRelatedList(portal_type="Internal Packing List Line"))
    )
    # Ensure that we don't have 2 new Internal Packing lists in the same second 
    sleep(5)
    self.login(source_administrator.getUserId())

    # We don't remove from Project if destination project is not provided
    self.assertEqual(computer.Computer_createMovement(), None)
    self.tic()

    self.assertEqual(computer.Item_getCurrentProjectValue(), None)
    self.assertEqual(computer.Item_getCurrentOwnerValue(), source_administrator)
    self.assertEqual(computer.Item_getCurrentSiteValue(), site)

    # Place in another project    
    self.assertEqual(computer.Computer_createMovement(
      destination=other_site.getRelativeUrl()), None)

    self.tic()
        
    self.assertEqual(3,
      len(computer.getAggregateRelatedList(portal_type="Internal Packing List Line"))
    )
    self.assertEqual(computer.Item_getCurrentProjectValue(), None)
    self.assertEqual(computer.Item_getCurrentOwnerValue(), source_administrator)
    self.assertEqual(computer.Item_getCurrentSiteValue(), other_site)

    self.assertEqual(3,
      len(computer.getAggregateRelatedList(portal_type="Internal Packing List Line"))
    )
    self.login(source_administrator.getUserId())

    # We don't remove from Project if destination project is not provided
    self.assertEqual(computer.Computer_createMovement(), None)
    self.tic()

    self.assertEqual(computer.Item_getCurrentProjectValue(), None)
    self.assertEqual(computer.Item_getCurrentOwnerValue(), source_administrator)
    self.assertEqual(computer.Item_getCurrentSiteValue(), other_site)

    self.assertEqual(4,
      len(computer.getAggregateRelatedList(portal_type="Internal Packing List Line"))
    )


class TestHostingSubscriptioncreateMovement(SlapOSTestCaseMixin):

  def _makeHostingSubscription(self):
    hosting_subscription = self.portal.hosting_subscription_module\
        .template_hosting_subscription.Base_createCloneDocument(batch_mode=1)
    hosting_subscription.validate()
    self.tic()
    return hosting_subscription

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

  def testUnauthorized(self):
    hosting_subscription = self._makeHostingSubscription()
    
    self.assertRaises(Unauthorized, hosting_subscription.HostingSubscription_createMovement)

    destination_section = self.makePerson(user=1)
    self.assertEqual(1 , len(destination_section.objectValues( portal_type="ERP5 Login")))

    self.login(destination_section.getUserId())
    self.assertRaises(Unauthorized, hosting_subscription.HostingSubscription_createMovement)

    self.login()
    other_user = self.makePerson(user=1)
    self.assertEqual(1 , len(other_user.objectValues(portal_type="ERP5 Login")))

    hosting_subscription.setDestinationSectionValue(destination_section)
    self.tic()

    self.assertRaises(Unauthorized, hosting_subscription.HostingSubscription_createMovement)
    self.login(other_user.getUserId())
    self.assertRaises(Unauthorized, hosting_subscription.HostingSubscription_createMovement)

    self.login(destination_section.getUserId())
    self.assertEqual(hosting_subscription.HostingSubscription_createMovement(), None)

  def test_project(self):
    hosting_subscription = self._makeHostingSubscription()
    destination_section = self.makePerson(user=1)
    hosting_subscription.setDestinationSectionValue(destination_section)

    project = self._makeProject()
    other_project = self._makeProject()
    self.tic()

    self.login(destination_section.getUserId())

    self.assertEqual(hosting_subscription.Item_getCurrentProjectValue(), None)
    self.assertEqual(hosting_subscription.Item_getCurrentOwnerValue(), None)
    self.assertEqual(hosting_subscription.Item_getCurrentSiteValue(), None)

    # Place in a project    
    self.assertEqual(hosting_subscription.HostingSubscription_createMovement(
      destination_project=project.getRelativeUrl()), None)

    self.tic()
    
    self.assertEqual(hosting_subscription.Item_getCurrentProjectValue(), project)
    self.assertEqual(hosting_subscription.Item_getCurrentOwnerValue(), destination_section)
    self.assertEqual(hosting_subscription.Item_getCurrentSiteValue(), None)

    self.assertEqual(1,
      len(hosting_subscription.getAggregateRelatedList(portal_type="Internal Packing List Line"))
    )

    # Ensure that we don't have 2 new Internal Packing lists in the same second 
    sleep(3)
    
    self.login(destination_section.getUserId())

    # We don't remove from Project if destination project is not provided
    self.assertEqual(hosting_subscription.HostingSubscription_createMovement(), None)
    self.tic()

    self.assertEqual(hosting_subscription.Item_getCurrentProjectValue(), project)
    self.assertEqual(hosting_subscription.Item_getCurrentOwnerValue(), destination_section)
    self.assertEqual(2,
      len(hosting_subscription.getAggregateRelatedList(portal_type="Internal Packing List Line"))
    )

    # Ensure that we don't have 2 new Internal Packing lists in the same second 
    sleep(3)
    
    # Place in another project    
    self.assertEqual(hosting_subscription.HostingSubscription_createMovement(
      destination_project=other_project.getRelativeUrl()), None)

    self.tic()
    
    self.assertEqual(hosting_subscription.Item_getCurrentProjectValue(), other_project)
    self.assertEqual(hosting_subscription.Item_getCurrentOwnerValue(), destination_section)
    self.assertEqual(hosting_subscription.Item_getCurrentSiteValue(), None)

    self.assertEqual(3,
      len(hosting_subscription.getAggregateRelatedList(portal_type="Internal Packing List Line"))
    )
    self.login(destination_section.getUserId())

    # Ensure that we don't have 2 new Internal Packing lists in the same second 
    sleep(3)
    
    # We don't remove from Project if destination project is not provided
    self.assertEqual(hosting_subscription.HostingSubscription_createMovement(), None)
    self.tic()

    self.assertEqual(hosting_subscription.Item_getCurrentProjectValue(), other_project)
    self.assertEqual(hosting_subscription.Item_getCurrentOwnerValue(), destination_section)
    self.assertEqual(hosting_subscription.Item_getCurrentSiteValue(), None)

    self.assertEqual(4,
      len(hosting_subscription.getAggregateRelatedList(portal_type="Internal Packing List Line"))
    )

  def test_owner(self):
    hosting_subscription = self._makeHostingSubscription()
    destination_section = self.makePerson(user=1)
    hosting_subscription.setDestinationSectionValue(destination_section)
    organisation = self._makeOrganisation()
    other_organisation = self._makeOrganisation()
    self.tic()

    self.login(destination_section.getUserId())

    self.assertEqual(hosting_subscription.Item_getCurrentProjectValue(), None)
    self.assertEqual(hosting_subscription.Item_getCurrentOwnerValue(), None)

    self.assertEqual(hosting_subscription.HostingSubscription_createMovement(
       destination=organisation.getRelativeUrl()), None)

    self.tic()
    
    self.assertEqual(hosting_subscription.Item_getCurrentProjectValue(), None)
    self.assertEqual(hosting_subscription.Item_getCurrentOwnerValue(), destination_section)
    self.assertEqual(hosting_subscription.Item_getCurrentSiteValue(), organisation)

    self.assertEqual(1,
      len(hosting_subscription.getAggregateRelatedList(portal_type="Internal Packing List Line"))
    )
    # Ensure that we don't have 2 new Internal Packing lists in the same second 
    sleep(3)
    self.login(destination_section.getUserId())

    self.assertEqual(hosting_subscription.HostingSubscription_createMovement(), None)
    self.tic()

    self.assertEqual(hosting_subscription.Item_getCurrentProjectValue(), None)
    self.assertEqual(hosting_subscription.Item_getCurrentOwnerValue(), destination_section)
    self.assertEqual(hosting_subscription.Item_getCurrentSiteValue(), organisation)

    # Ensure that we don't have 2 new Internal Packing lists in the same second 
    sleep(3)
    
    # Place in another project    
    self.assertEqual(hosting_subscription.HostingSubscription_createMovement(
      destination=other_organisation.getRelativeUrl()), None)

    self.tic()
        
    self.assertEqual(3,
      len(hosting_subscription.getAggregateRelatedList(portal_type="Internal Packing List Line"))
    )
    self.assertEqual(hosting_subscription.Item_getCurrentProjectValue(), None)
    self.assertEqual(hosting_subscription.Item_getCurrentOwnerValue(), destination_section)
    self.assertEqual(hosting_subscription.Item_getCurrentSiteValue(), other_organisation)

    self.assertEqual(3,
      len(hosting_subscription.getAggregateRelatedList(portal_type="Internal Packing List Line"))
    )
    self.login(destination_section.getUserId())

    # Ensure that we don't have 2 new Internal Packing lists in the same second 
    sleep(3)
    # We don't remove from Project if destination project is not provided
    self.assertEqual(hosting_subscription.HostingSubscription_createMovement(), None)
    self.tic()

    self.assertEqual(hosting_subscription.Item_getCurrentProjectValue(), None)
    self.assertEqual(hosting_subscription.Item_getCurrentOwnerValue(), destination_section)
    self.assertEqual(hosting_subscription.Item_getCurrentSiteValue(), other_organisation)

    self.assertEqual(4,
      len(hosting_subscription.getAggregateRelatedList(portal_type="Internal Packing List Line"))
    )
