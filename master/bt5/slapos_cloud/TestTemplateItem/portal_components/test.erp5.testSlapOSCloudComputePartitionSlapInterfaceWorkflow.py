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


class TestSlapOSCoreComputePartitionSlapInterfaceWorkflow(SlapOSTestCaseMixin):
  def afterSetUp(self):
    self.login()
    SlapOSTestCaseMixin.afterSetUp(self)
    # Clone compute_node document
    self.compute_node = self.portal.compute_node_module\
        .newContent(portal_type="Compute Node")
    self.compute_node.edit(
      title="compute node %s" % (self.new_id, ),
      reference="TESTCOMP-%s" % (self.new_id, ),
      allocation_scope='open',
      capacity_scope='open',
    )
    self.compute_node.validate()
    login = self.compute_node.newContent(
      portal_type="Certificate Login",
      reference=self.compute_node.getReference()
    )
    login.validate()

    # install an software release
    self.software_installation = self.portal.software_installation_module\
        .newContent(portal_type='Software Installation',
        url_string=self.generateNewSoftwareReleaseUrl(),
        aggregate=self.compute_node.getRelativeUrl())
    self.software_installation.validate()
    self.software_installation.requestStart()

    self.tic()
    self.login(self.compute_node.getUserId())

  def test_markFree(self):
    partition = self.compute_node.newContent(portal_type='Compute Partition',
        reference='PART-%s' % self.generateNewId())
    partition.validate()
    partition.markFree()
    self.tic()
    self.assertEqual(1, self.portal.portal_catalog.countResults(
        parent_uid=self.compute_node.getUid(), free_for_request=1)[0][0])

  def test_markFree_markBusy(self):
    partition = self.compute_node.newContent(portal_type='Compute Partition',
        reference='PART-%s' % self.generateNewId())
    partition.validate()
    partition.markFree()
    self.tic()
    self.assertEqual(1, self.portal.portal_catalog.countResults(
        parent_uid=self.compute_node.getUid(), free_for_request=1)[0][0])
    partition.markBusy()
    self.tic()
    self.assertEqual(0, self.portal.portal_catalog.countResults(
        parent_uid=self.compute_node.getUid(), free_for_request=1)[0][0])

  def test_markFree_markBusy_markFree(self):
    partition = self.compute_node.newContent(portal_type='Compute Partition',
        reference='PART-%s' % self.generateNewId())
    partition.validate()
    partition.markFree()
    self.tic()
    self.assertEqual(1, self.portal.portal_catalog.countResults(
        parent_uid=self.compute_node.getUid(), free_for_request=1)[0][0])
    partition.markBusy()
    self.tic()
    self.assertEqual(0, self.portal.portal_catalog.countResults(
        parent_uid=self.compute_node.getUid(), free_for_request=1)[0][0])
    partition.markFree()
    self.tic()
    self.assertEqual(1, self.portal.portal_catalog.countResults(
        parent_uid=self.compute_node.getUid(), free_for_request=1)[0][0])

  def test_markInactive(self):
    partition = self.compute_node.newContent(portal_type='Compute Partition',
        reference='PART-%s' % self.generateNewId())
    partition.validate()
    partition.markInactive()
    self.tic()
    self.assertEqual(0, self.portal.portal_catalog.countResults(
        parent_uid=self.compute_node.getUid(), free_for_request=1)[0][0])

  def test_markInactive_markFree(self):
    partition = self.compute_node.newContent(portal_type='Compute Partition',
        reference='PART-%s' % self.generateNewId())
    partition.validate()
    partition.markInactive()
    self.tic()
    self.assertEqual(0, self.portal.portal_catalog.countResults(
        parent_uid=self.compute_node.getUid(), free_for_request=1)[0][0])
    partition.markFree()
    self.tic()
    self.assertEqual(1, self.portal.portal_catalog.countResults(
        parent_uid=self.compute_node.getUid(), free_for_request=1)[0][0])
