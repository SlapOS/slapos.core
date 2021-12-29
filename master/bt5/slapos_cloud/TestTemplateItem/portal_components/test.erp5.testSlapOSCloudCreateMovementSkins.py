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

class TestInstanceTreecreateMovement(SlapOSTestCaseMixin):

  def _makeInstanceTree(self):
    instance_tree = self.portal.instance_tree_module\
        .template_instance_tree.Base_createCloneDocument(batch_mode=1)
    instance_tree.edit(reference='TESTINTT-%s' % instance_tree.getId(),
                       title='TESTINTT-%s' % instance_tree.getId())
    instance_tree.validate()
    self.tic()
    return instance_tree

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
    instance_tree = self._makeInstanceTree()
    
    self.assertRaises(Unauthorized, instance_tree.InstanceTree_createMovement)

    destination_section = self.makePerson(user=1)
    self.assertEqual(1 , len(destination_section.objectValues( portal_type="ERP5 Login")))

    self.login(destination_section.getUserId())
    self.assertRaises(Unauthorized, instance_tree.InstanceTree_createMovement)

    self.login()
    other_user = self.makePerson(user=1)
    self.assertEqual(1 , len(other_user.objectValues(portal_type="ERP5 Login")))

    instance_tree.setDestinationSectionValue(destination_section)
    self.tic()

    self.assertRaises(Unauthorized, instance_tree.InstanceTree_createMovement)
    self.login(other_user.getUserId())
    self.assertRaises(Unauthorized, instance_tree.InstanceTree_createMovement)

    self.login(destination_section.getUserId())
    self.assertEqual(instance_tree.InstanceTree_createMovement(), None)

  def test_project(self):
    instance_tree = self._makeInstanceTree()
    destination_section = self.makePerson(user=1)
    instance_tree.setDestinationSectionValue(destination_section)

    project = self._makeProject()
    other_project = self._makeProject()
    self.tic()

    self.login(destination_section.getUserId())

    self.assertEqual(instance_tree.Item_getCurrentProjectValue(), None)
    self.assertEqual(instance_tree.Item_getCurrentOwnerValue(), None)
    self.assertEqual(instance_tree.Item_getCurrentSiteValue(), None)

    # Place in a project    
    self.assertEqual(instance_tree.InstanceTree_createMovement(
      destination_project=project.getRelativeUrl()), None)

    self.tic()
    
    self.assertEqual(instance_tree.Item_getCurrentProjectValue(), project)
    self.assertEqual(instance_tree.Item_getCurrentOwnerValue(), destination_section)
    self.assertEqual(instance_tree.Item_getCurrentSiteValue(), None)

    self.assertEqual(1,
      len(instance_tree.getAggregateRelatedList(portal_type="Internal Packing List Line"))
    )

    # Ensure that we don't have 2 new Internal Packing lists in the same second 
    sleep(1)
    
    self.login(destination_section.getUserId())

    # We don't remove from Project if destination project is not provided
    self.assertEqual(instance_tree.InstanceTree_createMovement(), None)
    self.tic()

    self.assertEqual(instance_tree.Item_getCurrentProjectValue(), project)
    self.assertEqual(instance_tree.Item_getCurrentOwnerValue(), destination_section)
    self.assertEqual(2,
      len(instance_tree.getAggregateRelatedList(portal_type="Internal Packing List Line"))
    )

    # Ensure that we don't have 2 new Internal Packing lists in the same second 
    sleep(1)
    
    # Place in another project    
    self.assertEqual(instance_tree.InstanceTree_createMovement(
      destination_project=other_project.getRelativeUrl()), None)

    self.tic()
    
    self.assertEqual(instance_tree.Item_getCurrentProjectValue(), other_project)
    self.assertEqual(instance_tree.Item_getCurrentOwnerValue(), destination_section)
    self.assertEqual(instance_tree.Item_getCurrentSiteValue(), None)

    self.assertEqual(3,
      len(instance_tree.getAggregateRelatedList(portal_type="Internal Packing List Line"))
    )
    self.login(destination_section.getUserId())

    # Ensure that we don't have 2 new Internal Packing lists in the same second 
    sleep(1)
    
    # We don't remove from Project if destination project is not provided
    self.assertEqual(instance_tree.InstanceTree_createMovement(), None)
    self.tic()

    self.assertEqual(instance_tree.Item_getCurrentProjectValue(), other_project)
    self.assertEqual(instance_tree.Item_getCurrentOwnerValue(), destination_section)
    self.assertEqual(instance_tree.Item_getCurrentSiteValue(), None)

    self.assertEqual(4,
      len(instance_tree.getAggregateRelatedList(portal_type="Internal Packing List Line"))
    )

  def test_owner(self):
    instance_tree = self._makeInstanceTree()
    destination_section = self.makePerson(user=1)
    instance_tree.setDestinationSectionValue(destination_section)
    organisation = self._makeOrganisation()
    other_organisation = self._makeOrganisation()
    self.tic()

    self.login(destination_section.getUserId())

    self.assertEqual(instance_tree.Item_getCurrentProjectValue(), None)
    self.assertEqual(instance_tree.Item_getCurrentOwnerValue(), None)

    self.assertEqual(instance_tree.InstanceTree_createMovement(
       destination=organisation.getRelativeUrl()), None)

    self.tic()
    
    self.assertEqual(instance_tree.Item_getCurrentProjectValue(), None)
    self.assertEqual(instance_tree.Item_getCurrentOwnerValue(), destination_section)
    self.assertEqual(instance_tree.Item_getCurrentSiteValue(), organisation)

    self.assertEqual(1,
      len(instance_tree.getAggregateRelatedList(portal_type="Internal Packing List Line"))
    )
    # Ensure that we don't have 2 new Internal Packing lists in the same second 
    sleep(1)
    self.login(destination_section.getUserId())

    self.assertEqual(instance_tree.InstanceTree_createMovement(), None)
    self.tic()

    self.assertEqual(instance_tree.Item_getCurrentProjectValue(), None)
    self.assertEqual(instance_tree.Item_getCurrentOwnerValue(), destination_section)
    self.assertEqual(instance_tree.Item_getCurrentSiteValue(), organisation)

    # Ensure that we don't have 2 new Internal Packing lists in the same second 
    sleep(1)
    
    # Place in another project    
    self.assertEqual(instance_tree.InstanceTree_createMovement(
      destination=other_organisation.getRelativeUrl()), None)

    self.tic()
        
    self.assertEqual(3,
      len(instance_tree.getAggregateRelatedList(portal_type="Internal Packing List Line"))
    )
    self.assertEqual(instance_tree.Item_getCurrentProjectValue(), None)
    self.assertEqual(instance_tree.Item_getCurrentOwnerValue(), destination_section)
    self.assertEqual(instance_tree.Item_getCurrentSiteValue(), other_organisation)

    self.assertEqual(3,
      len(instance_tree.getAggregateRelatedList(portal_type="Internal Packing List Line"))
    )
    self.login(destination_section.getUserId())

    # Ensure that we don't have 2 new Internal Packing lists in the same second 
    sleep(1)
    # We don't remove from Project if destination project is not provided
    self.assertEqual(instance_tree.InstanceTree_createMovement(), None)
    self.tic()

    self.assertEqual(instance_tree.Item_getCurrentProjectValue(), None)
    self.assertEqual(instance_tree.Item_getCurrentOwnerValue(), destination_section)
    self.assertEqual(instance_tree.Item_getCurrentSiteValue(), other_organisation)

    self.assertEqual(4,
      len(instance_tree.getAggregateRelatedList(portal_type="Internal Packing List Line"))
    )
