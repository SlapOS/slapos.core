# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2012 Nexedi SA and Contributors. All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsibility of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# guarantees and support are strongly advised to contract a Free Software
# Service Company
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

class TestSlapOSCloudSkinsMixin(SlapOSTestCaseMixin):
  pass

class TestComputeNode_afterClone(TestSlapOSCloudSkinsMixin):

  def test_ComputeNode_afterClone(self):
    compute_node = self.portal.compute_node_module.newContent(
      portal_type="Compute Node",
      title="TESTCOMPUTERNODE-%s" % self.generateNewId())

    self.assertTrue(compute_node.hasUserId())
    self.assertTrue(compute_node.getUserId().startswith("C"))
    user_id = compute_node.getUserId()

    compute_node.ComputeNode_afterClone()
    self.assertTrue(compute_node.hasUserId())
    self.assertTrue(compute_node.getUserId().startswith("C"))
    self.assertNotEqual(compute_node.getUserId(), user_id)

    user_id = compute_node.getUserId()
    new_compute_node = compute_node.Base_createCloneDocument(batch_mode=1)
    self.assertTrue(new_compute_node.hasUserId())
    self.assertTrue(new_compute_node.getUserId().startswith("C"))
    self.assertNotEqual(new_compute_node.getUserId(), user_id)


class TestInstanceNode_afterClone(TestSlapOSCloudSkinsMixin):

  def test_InstanceNode_afterClone(self):
    instance_node = self.portal.compute_node_module.newContent(
      portal_type="Instance Node",
      title="TESTINSTANCENODE-%s" % self.generateNewId())
    instance_node.validate()

    reference = instance_node.getReference()
    instance_node.InstanceNode_afterClone()
    self.assertTrue(instance_node.getReference().startswith("SHARED-"))
    self.assertNotEqual(instance_node.getReference(), reference)

    reference = instance_node.getReference()
    new_instance_node = instance_node.Base_createCloneDocument(batch_mode=1)
    self.assertTrue(new_instance_node.getReference().startswith("SHARED-"))
    self.assertNotEqual(new_instance_node.getReference(), reference)


class TestRemoteNode_afterClone(TestSlapOSCloudSkinsMixin):

  def test_RemoteNode_afterClone(self):
    remote_node = self.portal.compute_node_module.newContent(
      portal_type="Remote Node",
      title="TESTREMOTENODE-%s" % self.generateNewId())
    remote_node.validate()

    reference = remote_node.getReference()
    remote_node.RemoteNode_afterClone()
    self.assertTrue(remote_node.getReference().startswith("REMOTE-"))
    self.assertNotEqual(remote_node.getReference(), reference)

    reference = remote_node.getReference()
    new_remote_node = remote_node.Base_createCloneDocument(batch_mode=1)
    remote_node.InstanceNode_afterClone()
    self.assertTrue(new_remote_node.getReference().startswith("REMOTE-"))
    self.assertNotEqual(new_remote_node.getReference(), reference)

class TestSoftwareInstance_afterClone(TestSlapOSCloudSkinsMixin):

  def test_SoftwareInstance_afterClone(self):
    instance = self.portal.software_instance_module.newContent(
      portal_type="Software Instance",
      title="TESTSOFTINST-%s" % self.generateNewId())
    instance.validate()

    self.assertTrue(instance.hasUserId())
    self.assertTrue(instance.getUserId().startswith("SI"))
    user_id = instance.getUserId()

    instance.SoftwareInstance_afterClone()
    self.assertTrue(instance.hasUserId())
    self.assertTrue(instance.getUserId().startswith("SI"))
    self.assertNotEqual(instance.getUserId(), user_id)

    user_id = instance.getUserId()
    new_instance = instance.Base_createCloneDocument(batch_mode=1)
    self.assertTrue(new_instance.hasUserId())
    self.assertTrue(new_instance.getUserId().startswith("SI"))
    self.assertNotEqual(new_instance.getUserId(), user_id)


class TestComputeNetwork_afterClone(TestSlapOSCloudSkinsMixin):

  def test_ComputerNetwork_afterClone(self):
    computer_network = self.portal.computer_network_module.newContent(
      portal_type="Computer Network",
      title="TESTNET-%s" % self.generateNewId())
    computer_network.approveRegistration()

    reference = computer_network.getReference()
    computer_network.ComputerNetwork_afterClone()
    self.assertTrue(reference.startswith("NET-"))
    # afterClone dont change already validated computer_network
    self.assertEqual(computer_network.getReference(), reference)

    new_computer_network = computer_network.Base_createCloneDocument(batch_mode=1)
    self.assertEqual(new_computer_network.getReference(), None)
    self.assertNotEqual(new_computer_network.getReference(), reference)

