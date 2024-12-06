# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2019 Nexedi SA and Contributors. All Rights Reserved.
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

class TestSlapOSPDMCreateUpgradeDecisionSkins(SlapOSTestCaseMixin):

  def test_createUpgradeDecision_destroyed_instance(self):
    instance_tree = self.portal.instance_tree_module.newContent(
      portal_type="Instance Tree"
    )
    self.portal.portal_workflow._jumpToStateFor(instance_tree,
                                                'destroy_requested')
    self.assertEqual(None, instance_tree.InstanceTree_createUpgradeDecision())

  def test_createUpgradeDecision_without_softwareProduct(self):
    instance_tree = self.portal.instance_tree_module.newContent(
      portal_type="Instance Tree"
    )
    self.assertEqual(None, instance_tree.InstanceTree_createUpgradeDecision())

  def checkCreatedUpgradeDecision(self, upgrade_decision, instance_tree,
                                  software_product, release_variation,
                                  type_variation):
    self.assertEqual('confirmed', upgrade_decision.getSimulationState())
    project = instance_tree.getFollowUpValue()
    self.assertEqual(instance_tree.getRelativeUrl(),
                     upgrade_decision.getAggregate())
    self.assertEqual(software_product.getRelativeUrl(),
                     upgrade_decision.getResource())
    self.assertEqual(release_variation.getRelativeUrl(),
                     upgrade_decision.getSoftwareRelease())
    self.assertEqual(type_variation.getRelativeUrl(),
                     upgrade_decision.getSoftwareType())
    self.assertEqual(project.getRelativeUrl(),
                     upgrade_decision.getDestinationProject())
    person = instance_tree.getDestinationSectionValue()
    self.assertEqual(person.getRelativeUrl(),
                     upgrade_decision.getDestinationDecision())
    self.assertEqual(person.getRelativeUrl(),
                     upgrade_decision.getDestinationSection())
    # Check that software release url is not the same
    self.assertEqual(type_variation.getTitle(),
                     instance_tree.getSourceReference())
    self.assertNotEqual(release_variation.getUrlString(),
                        instance_tree.getUrlString())

  ##########################################################################
  # Not allocated
  ##########################################################################
  def test_createUpgradeDecision_notAllocated_newReleaseOnComputeNode(self):
    software_product, _, type_variation, compute_node, _, instance_tree = self.bootstrapAllocableInstanceTree()
    self.tic()

    new_release_variation = self._makeSoftwareRelease(software_product)
    self.addAllocationSupply("for compute node", compute_node, software_product,
                             new_release_variation, type_variation, disable_alarm=True)
    self.tic()

    self.checkCreatedUpgradeDecision(
      instance_tree.InstanceTree_createUpgradeDecision(),
      instance_tree, software_product, new_release_variation, type_variation
    )

    # Ensure we are not upgrading for the same thing.
    _, allocation_cell_list = instance_tree.InstanceTree_getNodeAndAllocationSupplyCellList(
      software_product, new_release_variation, type_variation)

    self.assertEqual(len(allocation_cell_list), 1)
    self.assertNotEqual(
      allocation_cell_list[0].getSoftwareReleaseValue().getUrlString(),
      instance_tree.getUrlString())

    self.assertEqual(
      allocation_cell_list[0].getSoftwareReleaseValue().getUrlString(),
      new_release_variation.getUrlString())


  def test_createUpgradeDecision_notAllocated_newReleaseOnRemoteNode(self):
    software_product, _, type_variation, compute_node, _, instance_tree = self.bootstrapAllocableInstanceTree(node="remote")
    self.tic()

    new_release_variation = self._makeSoftwareRelease(software_product)
    self.addAllocationSupply("for remote node", compute_node, software_product,
                             new_release_variation, type_variation, disable_alarm=True)
    self.tic()

    self.checkCreatedUpgradeDecision(
      instance_tree.InstanceTree_createUpgradeDecision(),
      instance_tree, software_product, new_release_variation, type_variation
    )

    # Ensure we are not upgrading for the same thing.
    _, allocation_cell_list = instance_tree.InstanceTree_getNodeAndAllocationSupplyCellList(
      software_product, new_release_variation, type_variation)

    self.assertEqual(len(allocation_cell_list), 1)
    self.assertNotEqual(
      allocation_cell_list[0].getSoftwareReleaseValue().getUrlString(),
      instance_tree.getUrlString())

    self.assertEqual(
      allocation_cell_list[0].getSoftwareReleaseValue().getUrlString(),
      new_release_variation.getUrlString())

  def test_createUpgradeDecision_notAllocated_newReleaseOnInstanceNode(self):
    software_product, _, type_variation, compute_node, _, instance_tree = self.bootstrapAllocableInstanceTree(allocation_state="impossible", node="instance")
    self.tic()

    new_release_variation = self._makeSoftwareRelease(software_product)
    self.addAllocationSupply("for instance node", compute_node, software_product,
                             new_release_variation, type_variation, disable_alarm=True)
    self.tic()

    self.assertEqual(None, instance_tree.InstanceTree_createUpgradeDecision())

  def test_createUpgradeDecision_notAllocated_newReleaseOnComputeNodeWith2AllocationSupplies(self):
    software_product, _, type_variation, compute_node, _, instance_tree = self.bootstrapAllocableInstanceTree()
    self.tic()

    new_release_variation = self._makeSoftwareRelease(software_product)
    self.addAllocationSupply("for compute node", compute_node, software_product,
                             new_release_variation, type_variation, disable_alarm=True)
    self.addAllocationSupply("for compute node", compute_node, software_product,
                             new_release_variation, type_variation, disable_alarm=True)
    self.tic()

    self.checkCreatedUpgradeDecision(
      instance_tree.InstanceTree_createUpgradeDecision(),
      instance_tree, software_product, new_release_variation, type_variation
    )

    # Ensure we are not upgrading for the same thing.
    _, allocation_cell_list = instance_tree.InstanceTree_getNodeAndAllocationSupplyCellList(
      software_product, new_release_variation, type_variation)

    self.assertEqual(len(allocation_cell_list), 1)
    self.assertNotEqual(
      allocation_cell_list[0].getSoftwareReleaseValue().getUrlString(),
      instance_tree.getUrlString())

    self.assertEqual(
      allocation_cell_list[0].getSoftwareReleaseValue().getUrlString(),
      new_release_variation.getUrlString())

  def test_createUpgradeDecision_notAllocated_sameRelease(self):
    software_product, release_variation, type_variation, compute_node, _, instance_tree = self.bootstrapAllocableInstanceTree()
    self.tic()

    self.addAllocationSupply(
      "for compute node", compute_node, software_product,
      release_variation, type_variation, disable_alarm=True)

    self.assertEqual(None, instance_tree.InstanceTree_createUpgradeDecision())

  def test_createUpgradeDecision_notAllocated_twoRelease(self):
    software_product, release_variation, type_variation, compute_node, _, instance_tree = self.bootstrapAllocableInstanceTree()
    self.tic()

    self.addAllocationSupply(
      "for compute node", compute_node, software_product,
      release_variation, type_variation, disable_alarm=True)
    new_release_variation = self._makeSoftwareRelease(software_product)
    self.addAllocationSupply("for compute node 2", compute_node, software_product,
                             new_release_variation, type_variation, disable_alarm=True)
    self.tic()

    self.assertEqual(None, instance_tree.InstanceTree_createUpgradeDecision())

  def test_createUpgradeDecision_notAllocated_newRelease_ongoingDecision(self):
    software_product, _, type_variation, compute_node, _, instance_tree = self.bootstrapAllocableInstanceTree()
    self.tic()

    new_release_variation = self._makeSoftwareRelease(software_product)
    self.addAllocationSupply("for compute node 2", compute_node, software_product,
                             new_release_variation, type_variation, disable_alarm=True)
    self.tic()

    self.checkCreatedUpgradeDecision(
      instance_tree.InstanceTree_createUpgradeDecision(),
      instance_tree, software_product, new_release_variation, type_variation
    )
    self.tic()

    self.assertEqual(None, instance_tree.InstanceTree_createUpgradeDecision())

  def test_createUpgradeDecision_notAllocated_newRelease_ongoingDecisionActivity(self):
    software_product, _, type_variation, compute_node, _, instance_tree = self.bootstrapAllocableInstanceTree()
    self.tic()

    new_release_variation = self._makeSoftwareRelease(software_product)
    self.addAllocationSupply("for compute node 2", compute_node, software_product,
                             new_release_variation, type_variation, disable_alarm=True)
    self.tic()

    self.checkCreatedUpgradeDecision(
      instance_tree.InstanceTree_createUpgradeDecision(),
      instance_tree, software_product, new_release_variation, type_variation
    )
    self.commit()

    self.assertEqual(None, instance_tree.InstanceTree_createUpgradeDecision())

  def test_createUpgradeDecision_notAllocated_newRelease_cancelledDecision(self):
    software_product, _, type_variation, compute_node, _, instance_tree = self.bootstrapAllocableInstanceTree()
    self.tic()

    new_release_variation = self._makeSoftwareRelease(software_product)
    self.addAllocationSupply("for compute node 2", compute_node, software_product,
                             new_release_variation, type_variation, disable_alarm=True)
    self.tic()

    upgrade_decision = instance_tree.InstanceTree_createUpgradeDecision()
    self.checkCreatedUpgradeDecision(
      upgrade_decision,
      instance_tree, software_product, new_release_variation, type_variation
    )
    upgrade_decision.cancel()
    self.tic()

    self.checkCreatedUpgradeDecision(
      instance_tree.InstanceTree_createUpgradeDecision(),
      instance_tree, software_product, new_release_variation, type_variation
    )

  def test_createUpgradeDecision_notAllocated_newRelease_rejectedDecisionSameRelease(self):
    software_product, _, type_variation, compute_node, _, instance_tree = self.bootstrapAllocableInstanceTree()
    self.tic()

    new_release_variation = self._makeSoftwareRelease(software_product)
    self.addAllocationSupply("for compute node 2", compute_node, software_product,
                             new_release_variation, type_variation, disable_alarm=True)
    self.tic()

    upgrade_decision = instance_tree.InstanceTree_createUpgradeDecision()
    self.checkCreatedUpgradeDecision(
      upgrade_decision,
      instance_tree, software_product, new_release_variation, type_variation
    )
    upgrade_decision.reject()
    self.tic()

    self.assertEqual(None, instance_tree.InstanceTree_createUpgradeDecision())

  def test_createUpgradeDecision_notAllocated_newRelease_rejectedDecisionAnotherRelease(self):
    software_product, _, type_variation, compute_node, _, instance_tree = self.bootstrapAllocableInstanceTree()
    self.tic()

    new_release_variation = self._makeSoftwareRelease(software_product)
    supply = self.addAllocationSupply("for compute node 2", compute_node, software_product,
                             new_release_variation, type_variation, disable_alarm=True)
    self.tic()

    upgrade_decision = instance_tree.InstanceTree_createUpgradeDecision()
    self.checkCreatedUpgradeDecision(
      upgrade_decision,
      instance_tree, software_product, new_release_variation, type_variation
    )
    upgrade_decision.reject()
    supply.invalidate()
    self.tic()

    new_release_variation2 = self._makeSoftwareRelease(software_product)
    supply = self.addAllocationSupply("for compute node 3", compute_node, software_product,
                             new_release_variation2, type_variation, disable_alarm=True)
    self.tic()

    self.checkCreatedUpgradeDecision(
      instance_tree.InstanceTree_createUpgradeDecision(),
      instance_tree, software_product, new_release_variation2, type_variation
    )
  ##########################################################################
  # Shared not allocated
  ##########################################################################
  def test_createUpgradeDecision_sharedNotAllocated_newReleaseOnComputeNode(self):
    software_product, _, type_variation, compute_node, _, instance_tree = self.bootstrapAllocableInstanceTree(shared=True)
    self.tic()

    new_release_variation = self._makeSoftwareRelease(software_product)
    self.addAllocationSupply("for compute node", compute_node, software_product,
                             new_release_variation, type_variation, disable_alarm=True)
    self.tic()

    self.assertEqual(None, instance_tree.InstanceTree_createUpgradeDecision())

  def test_createUpgradeDecision_sharedNotAllocated_newReleaseOnRemoteNode(self):
    software_product, _, type_variation, compute_node, _, instance_tree = self.bootstrapAllocableInstanceTree(shared=True, node="remote")
    self.tic()

    new_release_variation = self._makeSoftwareRelease(software_product)
    self.addAllocationSupply("for remote node", compute_node, software_product,
                             new_release_variation, type_variation, disable_alarm=True)
    self.tic()

    self.checkCreatedUpgradeDecision(
      instance_tree.InstanceTree_createUpgradeDecision(),
      instance_tree, software_product, new_release_variation, type_variation
    )

  def test_createUpgradeDecision_sharedNotAllocated_newReleaseOnInstanceNode(self):
    software_product, _, type_variation, compute_node, _, instance_tree = self.bootstrapAllocableInstanceTree(shared=True, node="instance")
    self.tic()

    new_release_variation = self._makeSoftwareRelease(software_product)
    self.addAllocationSupply("for instance node", compute_node, software_product,
                             new_release_variation, type_variation, disable_alarm=True)
    self.tic()

    self.checkCreatedUpgradeDecision(
      instance_tree.InstanceTree_createUpgradeDecision(),
      instance_tree, software_product, new_release_variation, type_variation
    )

  ##########################################################################
  # Allocated on Compute Node
  ##########################################################################
  def test_createUpgradeDecision_allocatedOnComputeNode_newReleaseOnAnotherComputeNode(self):
    software_product, _, type_variation, _, _, instance_tree = self.bootstrapAllocableInstanceTree(allocation_state='allocated')

    project = instance_tree.getFollowUpValue()
    person = instance_tree.getDestinationSectionValue()

    person.requestComputeNode(compute_node_title='another test compute node',
                              project_reference=project.getReference())
    self.tic()
    compute_node2 = self.portal.portal_catalog.getResultValue(
      portal_type='Compute Node',
      reference=self.portal.REQUEST.get('compute_node_reference')
    )
    assert compute_node2 is not None

    new_release_variation = self._makeSoftwareRelease(software_product)
    self.addAllocationSupply("for compute node 2", compute_node2, software_product,
                             new_release_variation, type_variation, disable_alarm=True)
    self.tic()

    self.assertEqual(None, instance_tree.InstanceTree_createUpgradeDecision())

  def test_createUpgradeDecision_allocatedOnComputeNode_newReleaseOnComputeNode(self):
    software_product, _, type_variation, compute_node, _, instance_tree = self.bootstrapAllocableInstanceTree(allocation_state='allocated')

    new_release_variation = self._makeSoftwareRelease(software_product)
    self.addAllocationSupply("for compute node", compute_node, software_product,
                             new_release_variation, type_variation, disable_alarm=True)
    self.tic()

    self.checkCreatedUpgradeDecision(
      instance_tree.InstanceTree_createUpgradeDecision(),
      instance_tree, software_product, new_release_variation, type_variation
    )

  def test_createUpgradeDecision_allocatedOnComputeNode_newReleaseOnComputeNodeAndCorrectTarget(self):
    software_product, _, type_variation, compute_node, _, instance_tree = self.bootstrapAllocableInstanceTree(allocation_state='allocated')

    new_release_variation = self._makeSoftwareRelease(software_product)
    self.addAllocationSupply("for compute node", compute_node, software_product,
                             new_release_variation, type_variation, disable_alarm=True)
    self.tic()

    self.checkCreatedUpgradeDecision(
      instance_tree.InstanceTree_createUpgradeDecision(
        target_software_release=new_release_variation,
        target_software_type=type_variation
      ),
      instance_tree, software_product, new_release_variation, type_variation
    )

  def test_createUpgradeDecision_allocatedOnComputeNode_newReleaseOnComputeNodeAndIncorrectTarget(self):
    software_product, _, type_variation, compute_node, _, instance_tree = self.bootstrapAllocableInstanceTree(allocation_state='allocated')

    new_release_variation = self._makeSoftwareRelease(software_product)
    incorrect_release_variation = self._makeSoftwareRelease(software_product)
    self.addAllocationSupply("for compute node", compute_node, software_product,
                             new_release_variation, type_variation, disable_alarm=True)
    self.tic()

    self.assertEqual(
      None,
      instance_tree.InstanceTree_createUpgradeDecision(
        target_software_release=incorrect_release_variation,
        target_software_type=type_variation
      )
    )

  def test_createUpgradeDecision_allocatedOnComputeNode_twoRelease(self):
    software_product, release_variation, type_variation, compute_node, _, instance_tree = self.bootstrapAllocableInstanceTree(allocation_state='allocated')
    self.tic()

    self.addAllocationSupply(
      "for compute node", compute_node, software_product,
      release_variation, type_variation, disable_alarm=True)
    new_release_variation = self._makeSoftwareRelease(software_product)
    self.addAllocationSupply("for compute node 2", compute_node, software_product,
                             new_release_variation, type_variation, disable_alarm=True)
    self.tic()

    self.assertEqual(None, instance_tree.InstanceTree_createUpgradeDecision())

  def test_createUpgradeDecision_allocatedOnComputeNode_twoReleaseAndCorrectTarget(self):
    software_product, release_variation, type_variation, compute_node, _, instance_tree = self.bootstrapAllocableInstanceTree(allocation_state='allocated')
    self.tic()

    self.addAllocationSupply(
      "for compute node", compute_node, software_product,
      release_variation, type_variation, disable_alarm=True)
    new_release_variation = self._makeSoftwareRelease(software_product)
    self.addAllocationSupply("for compute node 2", compute_node, software_product,
                             new_release_variation, type_variation, disable_alarm=True)
    self.tic()

    self.checkCreatedUpgradeDecision(
      instance_tree.InstanceTree_createUpgradeDecision(
        target_software_release=new_release_variation,
        target_software_type=type_variation
      ),
      instance_tree, software_product, new_release_variation, type_variation
    )

  def test_createUpgradeDecision_allocatedOnComputeNode_twoReleaseAndIncorrectTarget(self):
    software_product, release_variation, type_variation, compute_node, _, instance_tree = self.bootstrapAllocableInstanceTree(allocation_state='allocated')
    self.tic()

    self.addAllocationSupply(
      "for compute node", compute_node, software_product,
      release_variation, type_variation, disable_alarm=True)
    new_release_variation = self._makeSoftwareRelease(software_product)
    incorrect_release_variation = self._makeSoftwareRelease(software_product)
    self.addAllocationSupply("for compute node 2", compute_node, software_product,
                             new_release_variation, type_variation, disable_alarm=True)
    self.tic()

    self.assertEqual(
      instance_tree.InstanceTree_createUpgradeDecision(
        target_software_release=incorrect_release_variation,
        target_software_type=type_variation
      ),
      None
    )

  ##########################################################################
  # Shared allocated on Compute Node
  ##########################################################################
  def test_createUpgradeDecision_slaveAllocatedOnComputeNodeSameTree_newReleaseOnComputeNodeButNotTree(self):
    software_product, _, type_variation, compute_node, _, instance_tree = self.bootstrapAllocableInstanceTree(allocation_state='allocated', shared=True)
    self.tic()

    new_release_variation = self._makeSoftwareRelease(software_product)
    self.addAllocationSupply("for compute node", compute_node, software_product,
                             new_release_variation, type_variation, disable_alarm=True)
    self.tic()

    self.assertEqual(None, instance_tree.InstanceTree_createUpgradeDecision())

  def test_createUpgradeDecision_slaveAllocatedOnComputeNodeSameTree_newReleaseOnComputeNode(self):
    # A Slave Instance can not be the root instance and allocated on the same tree
    # at the same time
    software_product, _, type_variation, compute_node, _, instance_tree = self.bootstrapAllocableInstanceTree(allocation_state='allocated', shared=True)
    self.tic()

    new_release_variation = self._makeSoftwareRelease(software_product)
    self.addAllocationSupply("for compute node", compute_node, software_product,
                             new_release_variation, type_variation,
                             is_slave_on_same_instance_tree_allocable=True, disable_alarm=True)
    self.tic()

    self.assertEqual(None, instance_tree.InstanceTree_createUpgradeDecision())

  ##########################################################################
  # Allocated on Remote Node
  ##########################################################################
  def test_createUpgradeDecision_allocatedOnRemoteNode_newReleaseOnRemoteNode(self):
    software_product, _, type_variation, remote_node, _, instance_tree = self.bootstrapAllocableInstanceTree(allocation_state='allocated', node="remote")
    self.tic()

    new_release_variation = self._makeSoftwareRelease(software_product)
    self.addAllocationSupply("for remote node", remote_node, software_product,
                             new_release_variation, type_variation, disable_alarm=True)
    self.tic()

    self.checkCreatedUpgradeDecision(
      instance_tree.InstanceTree_createUpgradeDecision(),
      instance_tree, software_product, new_release_variation, type_variation
    )

  def test_createUpgradeDecision_allocatedOnRemoteNode_twoRelease(self):
    software_product, release_variation, type_variation, remote_node, _, instance_tree = self.bootstrapAllocableInstanceTree(allocation_state='allocated', node="remote")
    self.tic()

    self.addAllocationSupply(
      "for remote node", remote_node, software_product,
      release_variation, type_variation, disable_alarm=True)
    new_release_variation = self._makeSoftwareRelease(software_product)
    self.addAllocationSupply("for compute node 2", remote_node, software_product,
                             new_release_variation, type_variation, disable_alarm=True)
    self.tic()

    self.assertEqual(None, instance_tree.InstanceTree_createUpgradeDecision())

  def test_createUpgradeDecision_allocatedOnRemoteNode_newReleaseOnAnoterRemoteNode(self):
    software_product, _, type_variation, _, _, instance_tree = self.bootstrapAllocableInstanceTree(allocation_state='allocated', node="remote")
    self.tic()

    project = instance_tree.getFollowUpValue()
    remote_node2 = self.portal.compute_node_module.newContent(
      portal_type="Remote Node",
      follow_up_value=project
    )

    new_release_variation = self._makeSoftwareRelease(software_product)
    self.addAllocationSupply("for remote node 2", remote_node2, software_product,
                             new_release_variation, type_variation, disable_alarm=True)
    self.tic()

    self.assertEqual(None, instance_tree.InstanceTree_createUpgradeDecision())

  ##########################################################################
  # Shared allocated on Remote Node
  ##########################################################################
  def test_createUpgradeDecision_slaveAllocatedOnRemoteNode_newReleaseOnComputeNode(self):
    software_product, _, type_variation, remote_node, _, instance_tree = self.bootstrapAllocableInstanceTree(allocation_state='allocated', shared=True, node="remote")
    self.tic()

    new_release_variation = self._makeSoftwareRelease(software_product)
    self.addAllocationSupply("for remote node", remote_node, software_product,
                             new_release_variation, type_variation, disable_alarm=True)
    self.tic()

    self.checkCreatedUpgradeDecision(
      instance_tree.InstanceTree_createUpgradeDecision(),
      instance_tree, software_product, new_release_variation, type_variation
    )

  def test_createUpgradeDecision_slaveAllocatedOnRemoteNode_twoRelease(self):
    software_product, release_variation, type_variation, remote_node, _, instance_tree = self.bootstrapAllocableInstanceTree(allocation_state='allocated', shared=True, node="remote")
    self.tic()

    self.addAllocationSupply(
      "for remote node", remote_node, software_product,
      release_variation, type_variation, disable_alarm=True)
    new_release_variation = self._makeSoftwareRelease(software_product)
    self.addAllocationSupply("for compute node 2", remote_node, software_product,
                             new_release_variation, type_variation, disable_alarm=True)
    self.tic()

    self.assertEqual(None, instance_tree.InstanceTree_createUpgradeDecision())

  def test_createUpgradeDecision_slaveAllocatedOnRemoteNode_newReleaseOnAnoterRemoteNode(self):
    software_product, _, type_variation, _, _, instance_tree = self.bootstrapAllocableInstanceTree(allocation_state='allocated', shared=True, node="remote")
    self.tic()

    project = instance_tree.getFollowUpValue()
    remote_node2 = self.portal.compute_node_module.newContent(
      portal_type="Remote Node",
      follow_up_value=project
    )

    new_release_variation = self._makeSoftwareRelease(software_product)
    self.addAllocationSupply("for remote node 2", remote_node2, software_product,
                             new_release_variation, type_variation, disable_alarm=True)
    self.tic()

    self.assertEqual(None, instance_tree.InstanceTree_createUpgradeDecision())

  ##########################################################################
  # Shared allocated on Instance Node
  ##########################################################################
  def test_createUpgradeDecision_slaveAllocatedOnInstanceNode_newReleaseOnInstanceNode(self):
    software_product, _, type_variation, compute_node, _, instance_tree = self.bootstrapAllocableInstanceTree(allocation_state='allocated', shared=True, node="instance")
    self.tic()

    new_release_variation = self._makeSoftwareRelease(software_product)
    self.addAllocationSupply("for compute node", compute_node, software_product,
                             new_release_variation, type_variation, disable_alarm=True)
    self.tic()

    self.checkCreatedUpgradeDecision(
      instance_tree.InstanceTree_createUpgradeDecision(),
      instance_tree, software_product, new_release_variation, type_variation
    )
  def test_createUpgradeDecision_slaveAllocatedOnInstanceNode_newReleaseOnAnotherInstanceNode(self):
    software_product, _, type_variation, _, _, instance_tree = self.bootstrapAllocableInstanceTree(allocation_state='allocated', shared=True, node="instance")
    self.tic()

    project = instance_tree.getFollowUpValue()
    instance_node2 = self.portal.compute_node_module.newContent(
      portal_type="Instance Node",
      follow_up_value=project
    )
    new_release_variation = self._makeSoftwareRelease(software_product)
    self.addAllocationSupply("for compute node", instance_node2, software_product,
                             new_release_variation, type_variation, disable_alarm=True)
    self.tic()

    self.assertEqual(None, instance_tree.InstanceTree_createUpgradeDecision())
