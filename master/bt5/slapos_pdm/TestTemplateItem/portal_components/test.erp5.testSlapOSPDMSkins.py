# -*- coding:utf-8 -*-
##############################################################################
#
# Copyright (c) 2002-2013 Nexedi SA and Contributors. All Rights Reserved.
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

class TestSlapOSPDMSkins(SlapOSTestCaseMixin):
  require_certificate = 1

  def test_requestUpgrade(self):
    software_product, _, type_variation, compute_node, _, instance_tree = self.bootstrapAllocableInstanceTree()
    self.tic()

    new_release_variation = self._makeSoftwareRelease(software_product)
    self.addAllocationSupply("for compute node", compute_node, software_product,
                             new_release_variation, type_variation, disable_alarm=True)
    self.tic()

    upgrade_decision = instance_tree.InstanceTree_createUpgradeDecision()
    upgrade_decision.start()
    self.portal.portal_workflow._jumpToStateFor(instance_tree,
                                                'stop_requested')

    upgrade_decision.UpgradeDecision_processUpgrade()

    self.assertEqual(new_release_variation.getUrlString(),
                     instance_tree.getUrlString())
    self.assertEqual('stop_requested', instance_tree.getSlapState())
    self.assertEqual('delivered', upgrade_decision.getSimulationState())

  def test_requestUpgrade_destroyed_instance_tree(self):
    software_product, _, type_variation, compute_node, _, instance_tree = self.bootstrapAllocableInstanceTree()
    self.tic()

    new_release_variation = self._makeSoftwareRelease(software_product)
    self.addAllocationSupply("for compute node", compute_node, software_product,
                             new_release_variation, type_variation, disable_alarm=True)
    self.tic()

    upgrade_decision = instance_tree.InstanceTree_createUpgradeDecision()
    upgrade_decision.start()

    self.portal.portal_workflow._jumpToStateFor(instance_tree,
                                                'destroy_requested')

    upgrade_decision.UpgradeDecision_processUpgrade()

    self.assertNotEqual(new_release_variation.getUrlString(),
                        instance_tree.getUrlString())
    self.assertEqual('destroy_requested', instance_tree.getSlapState())
    self.assertEqual('rejected', upgrade_decision.getSimulationState())
