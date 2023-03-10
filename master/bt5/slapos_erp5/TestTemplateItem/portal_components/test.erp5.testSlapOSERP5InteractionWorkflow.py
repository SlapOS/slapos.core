# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2020 Nexedi SA and Contributors. All Rights Reserved.
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

class TestSlapOSERP5InteractionWorkflowComputeNodeSetAllocationScope(
    SlapOSTestCaseMixin):

  def _test_ComputeNode_setAllocationScope_public(self,
                                              allocation_scope="open/public",
                                              source_administration=None):
    compute_node = self.portal.compute_node_module.newContent(portal_type='Compute Node')

    compute_node.edit(capacity_scope=None,
                  monitor_scope=None,
                  source_administration=source_administration)
    self.commit()
    compute_node.edit(allocation_scope=allocation_scope)

    self.commit()
    self.assertEqual(compute_node.getCapacityScope(), 'close')
    self.assertEqual(compute_node.getMonitorScope(), 'enabled')
    self.commit()
    compute_node.edit(allocation_scope=None)
    self.commit()
    
    compute_node.edit(capacity_scope="open", monitor_scope='enabled')
    self.commit()

    compute_node.edit(allocation_scope=allocation_scope)
    self.commit()

    self.assertEqual(compute_node.getCapacityScope(), 'close')
    self.assertEqual(compute_node.getMonitorScope(), 'enabled')

    return compute_node

  def test_ComputeNode_setAllocationScope_public_no_source_adm(self):
    self._test_ComputeNode_setAllocationScope_public()

  def test_ComputeNode_setAllocationScope_subscription_no_source_adm(self):
    self._test_ComputeNode_setAllocationScope_public(
      allocation_scope="open/subscription"
    )

  def test_ComputeNode_setAllocationScope_personal(self,
                                              source_administration=None):
    compute_node = self.portal.compute_node_module.newContent(portal_type='Compute Node',
                  capacity_scope=None,
                  monitor_scope=None,
                  source_administration=source_administration)

    self.commit()
    compute_node.edit(allocation_scope='open/personal')

    self.commit()
    self.assertEqual(compute_node.getCapacityScope(), 'close')
    self.assertEqual(compute_node.getMonitorScope(), 'enabled')
    self.commit()
    compute_node.edit(allocation_scope=None)
    self.commit()
    
    compute_node.edit(capacity_scope="open")
    self.commit()

    compute_node.edit(allocation_scope='open/personal')
    self.commit()

    self.assertEqual(compute_node.getCapacityScope(), 'close')
    self.assertEqual(compute_node.getMonitorScope(), 'enabled')
    return compute_node

  def _test_ComputeNode_setAllocationScope_closed(self,
                                              source_administration=None,
                                              allocation_scope="close/forever",
                                              monitor_scope='enabled'):
    compute_node = self.portal.compute_node_module.newContent(portal_type='Compute Node',
                  capacity_scope=None,
                  monitor_scope=None,
                  source_administration=source_administration)

    self.commit()
    compute_node.edit(allocation_scope=allocation_scope)

    self.commit()
    self.assertEqual(compute_node.getCapacityScope(), 'close')
    self.assertEqual(compute_node.getMonitorScope(), monitor_scope)

    self.commit()
    compute_node.edit(allocation_scope=None)
    self.commit()
    
    compute_node.edit(capacity_scope="open")
    self.commit()

    compute_node.edit(allocation_scope=allocation_scope)
    self.commit()

    self.assertEqual(compute_node.getCapacityScope(), 'close')
    self.assertEqual(compute_node.getMonitorScope(), monitor_scope)
    return compute_node


  def test_ComputeNode_setAllocationScope_closed_forever(self):
    self._test_ComputeNode_setAllocationScope_closed(monitor_scope='disabled')

  def test_ComputeNode_setAllocationScope_closed_termination(self):
    self._test_ComputeNode_setAllocationScope_closed(
      allocation_scope="close/termination",
    )

  def test_ComputeNode_setAllocationScope_closed_outdated(self):
    self._test_ComputeNode_setAllocationScope_closed(
      allocation_scope="close/outdated",
    )

  def test_ComputeNode_setAllocationScope_closed_maintenance(self):
    self._test_ComputeNode_setAllocationScope_closed(
      allocation_scope="close/maintenance",
    )

  def test_ComputeNode_setAllocationScope_closed_noallocation(self):
    self._test_ComputeNode_setAllocationScope_closed(
      allocation_scope="close/noallocation",
    )