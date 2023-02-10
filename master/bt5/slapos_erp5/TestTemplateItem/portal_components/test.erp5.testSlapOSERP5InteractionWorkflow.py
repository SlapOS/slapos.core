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

  def test_ComputeNode_setAllocationScope_public_with_source_adm(self):
    person = self.makePerson()
    self.assertNotIn(person.getDefaultEmailCoordinateText(), [None, ""])

    compute_node = self._test_ComputeNode_setAllocationScope_public(
      source_administration=person.getRelativeUrl())

    self.assertEqual(compute_node.getSubjectList(), [''])
    self.assertEqual(compute_node.getDestinationSection(), None)

  def test_ComputeNode_setAllocationScope_subscription_with_source_adm(self):
    person = self.makePerson()
    self.assertNotIn(person.getDefaultEmailCoordinateText(), [None, ""])

    compute_node = self._test_ComputeNode_setAllocationScope_public(
      source_administration=person.getRelativeUrl(),
      allocation_scope="open/subscription")

    self.assertEqual(compute_node.getSubjectList(), [''])
    self.assertEqual(compute_node.getDestinationSection(), None)


  def _test_ComputeNode_setAllocationScope_personal(self,
                                              source_administration=None,
                                              subject_list=None):
    compute_node = self.portal.compute_node_module.newContent(portal_type='Compute Node',
                  capacity_scope=None,
                  monitor_scope=None,
                  source_administration=source_administration)
    if subject_list:
      compute_node.setSubjectList(subject_list)
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

  def test_ComputeNode_setAllocationScope_personal(self):
    compute_node = self._test_ComputeNode_setAllocationScope_personal()
    self.assertEqual(compute_node.getSubjectList(), [])
    self.assertEqual(compute_node.getDestinationSection(), None)

  def test_ComputeNode_setAllocationScope_personal_with_source_adm(self):
    person = self.makePerson()
    self.tic()

    self.assertNotIn(person.getDefaultEmailCoordinateText(), [None, ""])
    compute_node = self._test_ComputeNode_setAllocationScope_personal(
      source_administration=person.getRelativeUrl(),
    )
    self.assertEqual(compute_node.getSubjectList(), [person.getDefaultEmailCoordinateText()])
    self.assertEqual(compute_node.getDestinationSectionList(),
     [person.getRelativeUrl()])

  def test_ComputeNode_setAllocationScope_personal_with_subject_list(self):
    person = self.makePerson()
    self.tic()

    self.assertNotIn(person.getDefaultEmailCoordinateText(), [None, ""])
    compute_node = self._test_ComputeNode_setAllocationScope_personal(
      source_administration=person.getRelativeUrl(),
      subject_list=["some@example.com"]
    )
    self.assertEqual(compute_node.getSubjectList(), [person.getDefaultEmailCoordinateText()])
    self.assertEqual(compute_node.getDestinationSectionList(),
     [person.getRelativeUrl()])

  def _test_ComputeNode_setAllocationScope_friend(self,
                                              source_administration=None,
                                              subject_list=None):
    compute_node = self.portal.compute_node_module.newContent(portal_type='Compute Node')

    compute_node.edit(capacity_scope=None,
                  monitor_scope=None,
                  source_administration=source_administration)

    if subject_list:
      compute_node.setSubjectList(subject_list)

    self.commit()
    compute_node.edit(allocation_scope='open/friend')

    self.commit()
    self.assertEqual(compute_node.getCapacityScope(), 'close')
    self.assertEqual(compute_node.getMonitorScope(), 'enabled')
    self.commit()
    compute_node.edit(allocation_scope=None)
    self.commit()
    
    compute_node.edit(capacity_scope="open")
    self.commit()

    compute_node.edit(allocation_scope='open/friend')
    self.commit()

    self.assertEqual(compute_node.getCapacityScope(), 'close')
    self.assertEqual(compute_node.getMonitorScope(), 'enabled')
    return compute_node

  def test_ComputeNode_setAllocationScope_friend_with_source_adm(self):
    person = self.makePerson()
    self.tic()
    self.assertNotIn(person.getDefaultEmailCoordinateText(), [None, ""])

    compute_node = self._test_ComputeNode_setAllocationScope_friend(
      source_administration=person.getRelativeUrl())

    self.assertEqual(compute_node.getSubjectList(), [person.getDefaultEmailCoordinateText()])
    self.assertEqual(compute_node.getDestinationSectionList(),
     [person.getRelativeUrl()])

  def test_ComputeNode_setAllocationScope_friend_with_subject_list(self):
    person = self.makePerson()
    self.tic()
    self.assertNotIn(person.getDefaultEmailCoordinateText(), [None, ""])

    compute_node = self._test_ComputeNode_setAllocationScope_friend(
      source_administration=person.getRelativeUrl(),
      subject_list=["some@example.com"]
    )

    self.assertSameSet(compute_node.getSubjectList(),
                      ['some@example.com', person.getDefaultEmailCoordinateText()])

    self.assertEqual(compute_node.getDestinationSectionList(),
     [person.getRelativeUrl()])


  def _test_ComputeNode_setAllocationScope_closed(self,
                                              source_administration=None,
                                              allocation_scope="close/forever",
                                              subject_list=None,
                                              monitor_scope='enabled'):
    compute_node = self.portal.compute_node_module.newContent(portal_type='Compute Node',
                  capacity_scope=None,
                  monitor_scope=None,
                  source_administration=source_administration)
    if subject_list:
      compute_node.setSubjectList(subject_list)
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


  def test_ComputeNode_setAllocationScope_closed_forever_no_source_adm(self):
    self._test_ComputeNode_setAllocationScope_closed(monitor_scope='disabled')

  def test_ComputeNode_setAllocationScope_closed_forever_with_source_adm(self):
    person = self.makePerson()
    self.tic()
    self.assertNotIn(person.getDefaultEmailCoordinateText(), [None, ""])

    compute_node = self._test_ComputeNode_setAllocationScope_closed(
      source_administration=person.getRelativeUrl(), monitor_scope='disabled')

    self.assertEqual(compute_node.getSubjectList(), [person.getDefaultEmailCoordinateText()])
    self.assertEqual(compute_node.getDestinationSectionList(),
     [person.getRelativeUrl()])

  def test_ComputeNode_setAllocationScope_closed_termination_no_source_adm(self):
    self._test_ComputeNode_setAllocationScope_closed(
      allocation_scope="close/termination",
    )

  def test_ComputeNode_setAllocationScope_closed_termination_with_source_adm(self):
    person = self.makePerson()
    self.tic()
    self.assertNotIn(person.getDefaultEmailCoordinateText(), [None, ""])

    compute_node = self._test_ComputeNode_setAllocationScope_closed(
      allocation_scope="close/termination",
      source_administration=person.getRelativeUrl())

    self.assertEqual(compute_node.getSubjectList(), [person.getDefaultEmailCoordinateText()])
    self.assertEqual(compute_node.getDestinationSectionList(),
     [person.getRelativeUrl()])

  def test_ComputeNode_setAllocationScope_closed_outdated_no_source_adm(self):
    self._test_ComputeNode_setAllocationScope_closed(
      allocation_scope="close/outdated",
    )

  def test_ComputeNode_setAllocationScope_closed_outdated_with_source_adm(self):
    person = self.makePerson()
    self.tic()
    self.assertNotIn(person.getDefaultEmailCoordinateText(), [None, ""])

    compute_node = self._test_ComputeNode_setAllocationScope_closed(
      allocation_scope="close/outdated",
      source_administration=person.getRelativeUrl())

    self.assertEqual(compute_node.getSubjectList(), [person.getDefaultEmailCoordinateText()])
    self.assertEqual(compute_node.getDestinationSectionList(),
     [person.getRelativeUrl()])

  def test_ComputeNode_setAllocationScope_closed_maintenance_no_source_adm(self):
    self._test_ComputeNode_setAllocationScope_closed(
      allocation_scope="close/maintenance",
    )

  def test_ComputeNode_setAllocationScope_closed_maintenance_with_source_adm(self):
    person = self.makePerson()
    self.tic()
    self.assertNotIn(person.getDefaultEmailCoordinateText(), [None, ""])

    compute_node = self._test_ComputeNode_setAllocationScope_closed(
      allocation_scope="close/maintenance",
      source_administration=person.getRelativeUrl())

    self.assertEqual(compute_node.getSubjectList(), [person.getDefaultEmailCoordinateText()])
    self.assertEqual(compute_node.getDestinationSectionList(),
     [person.getRelativeUrl()])

  def test_ComputeNode_setAllocationScope_closed_noallocation_no_source_adm(self):
    self._test_ComputeNode_setAllocationScope_closed(
      allocation_scope="close/noallocation",
    )

  def test_ComputeNode_setAllocationScope_closed_noallocation_with_source_adm(self):
    person = self.makePerson()
    self.tic()
    self.assertNotIn(person.getDefaultEmailCoordinateText(), [None, ""])

    compute_node = self._test_ComputeNode_setAllocationScope_closed(
      allocation_scope="close/noallocation",
      source_administration=person.getRelativeUrl())

    self.assertEqual(compute_node.getSubjectList(), [person.getDefaultEmailCoordinateText()])
    self.assertEqual(compute_node.getDestinationSectionList(),
     [person.getRelativeUrl()])