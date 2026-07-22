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

  def _makeSoftwareInstance(self, partition, state='start_requested'):
    project = self.addProject()
    instance_tree = self.portal.instance_tree_module.newContent(
      portal_type="Instance Tree",
      title="TEST-%s" % self.generateNewId(),
      reference="TESTIT-%s" % self.generateNewId(),
      follow_up_value=project
    )
    software_type = "TYPE-%s" % self.generateNewId()
    new_id = self.generateNewId()
    instance = self.portal.software_instance_module.newContent(
      portal_type="Software Instance",
      title=instance_tree.getTitle(),
      reference="TESTSI-%s" % new_id,
      source_reference=software_type,
      url_string=self.generateNewSoftwareReleaseUrl(),
      text_content=self.generateSafeXml(),
      sla_xml=self.generateEmptyXml(),
      ssl_certificate="CERT-%s" % new_id,
      ssl_key="KEY-%s" % new_id,
      follow_up_value=project,
      specialise_value=instance_tree,
      destination_reference="DEST-%s" % new_id
    )
    instance.validate()
    instance.edit(aggregate=partition.getRelativeUrl())
    instance_tree.setSuccessorValue(instance)
    partition.markBusy()
    self.portal.portal_workflow._jumpToStateFor(instance, state)
    self.tic()
    return instance_tree, instance, software_type

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
    # It dont change because id is the same
    self.assertEqual(instance_node.getReference(), reference)

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
    # It dont change because id is the same
    self.assertEqual(remote_node.getReference(), reference)

    reference = remote_node.getReference()
    new_remote_node = remote_node.Base_createCloneDocument(batch_mode=1)
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


class TestComputePartition_getSoftwareType(TestSlapOSCloudSkinsMixin):

  def test_computePartitionGetSoftwareTypeNoInstance(self):
    _, partition = self._makeComputeNode(self.addProject())
    self.assertEqual(partition.ComputePartition_getSoftwareType(), "")

  def test_computePartitionGetSoftwareTypeStartRequested(self):
    _, partition = self._makeComputeNode(self.addProject())
    _, _, software_type = self._makeSoftwareInstance(partition, 'start_requested')
    self.assertEqual(partition.ComputePartition_getSoftwareType(), software_type)

  def test_computePartitionGetSoftwareTypeStopRequested(self):
    _, partition = self._makeComputeNode(self.addProject())
    _, _, software_type = self._makeSoftwareInstance(partition, 'stop_requested')
    self.assertEqual(partition.ComputePartition_getSoftwareType(), software_type)

  def test_computePartitionGetSoftwareTypeInvalidated(self):
    _, partition = self._makeComputeNode(self.addProject())
    _, instance, _ = self._makeSoftwareInstance(partition, 'start_requested')
    instance.invalidate()
    self.tic()
    self.assertEqual(partition.ComputePartition_getSoftwareType(), "")


class TestInstanceTree_getRootInstance(TestSlapOSCloudSkinsMixin):

  def test_getRootInstanceWrongTitle(self):
    _, partition = self._makeComputeNode(self.addProject())
    instance_tree, _, _ = self._makeSoftwareInstance(partition)
    instance_tree.setTitle("NOMATCH-%s" % self.generateNewId())
    self.tic()
    self.assertIsNone(instance_tree.InstanceTree_getRootInstance())

  def test_getRootInstanceMatch(self):
    _, partition = self._makeComputeNode(self.addProject())
    instance_tree, instance, _ = self._makeSoftwareInstance(partition)
    self.assertEqual(instance_tree.InstanceTree_getRootInstance(), instance)

  def test_getRootInstanceNoSucessor(self):
    _, partition = self._makeComputeNode(self.addProject())
    instance_tree, _, _ = self._makeSoftwareInstance(partition)
    instance_tree.setSuccessorValue(None)
    self.tic()
    self.assertIsNone(instance_tree.InstanceTree_getRootInstance())

  def test_getRootInstanceDestroyRequested(self):
    _, partition = self._makeComputeNode(self.addProject())
    instance_tree, instance, _ = self._makeSoftwareInstance(partition)
    self.portal.portal_workflow._jumpToStateFor(instance, 'destroy_requested')
    self.tic()
    self.assertIsNone(instance_tree.InstanceTree_getRootInstance())

  def test_getRootInstancePortalTypeFilter(self):
    _, partition = self._makeComputeNode(self.addProject())
    instance_tree, _, _ = self._makeSoftwareInstance(partition)
    self.assertIsNone(instance_tree.InstanceTree_getRootInstance(portal_type='Slave Instance'))

  def test_getRootInstancePortalTypeMatch(self):
    _, partition = self._makeComputeNode(self.addProject())
    instance_tree, instance, _ = self._makeSoftwareInstance(partition)
    self.assertEqual(instance_tree.InstanceTree_getRootInstance(portal_type='Software Instance'), instance)


class TestComputePartition_isFreeForRequest(TestSlapOSCloudSkinsMixin):

  def test_isFreeForRequestFree(self):
    _, partition = self._makeComputeNode(self.addProject())
    self.assertEqual(partition.ComputePartition_isFreeForRequest(), 1)

  def test_isFreeForRequestBusy(self):
    _, partition = self._makeComputeNode(self.addProject())
    self._makeSoftwareInstance(partition, 'start_requested')
    self.assertEqual(partition.ComputePartition_isFreeForRequest(), 0)


class TestBase_castDictToXMLString(TestSlapOSCloudSkinsMixin):

  def test_castDictToXMLStringSimple(self):
    result = self.portal.Base_castDictToXMLString({'key1': 'value1', 'key2': 'value2'})
    self.assertIn('key1', result)
    self.assertIn('value1', result)
    self.assertIn('key2', result)
    self.assertIn('value2', result)
    self.assertIn('<instance>', result)
    self.assertIn('</instance>', result)

  def test_castDictToXMLStringEmpty(self):
    result = self.portal.Base_castDictToXMLString({})
    self.assertIn('<instance', result)

  def test_castDictToXMLStringSingleParameter(self):
    result = self.portal.Base_castDictToXMLString({'url': 'http://example.com'})
    self.assertIn('<parameter id="url">', result)
    self.assertIn('http://example.com', result)

  def test_castDictToXMLStringIntegerValue(self):
    result = self.portal.Base_castDictToXMLString({'port': 8080})
    self.assertIn('8080', result)

  def test_castDictToXMLStringNoneValue(self):
    result = self.portal.Base_castDictToXMLString({'empty': None})
    self.assertIn('None', result)

  def test_castDictToXMLStringSortedKeys(self):
    result = self.portal.Base_castDictToXMLString({'z': '1', 'a': '2', 'm': '3'})
    z_pos = result.find('id="z"')
    a_pos = result.find('id="a"')
    m_pos = result.find('id="m"')
    self.assertGreater(z_pos, m_pos)
    self.assertGreater(m_pos, a_pos)

class TestBase_TransactionalTag(TestSlapOSCloudSkinsMixin):

  def test_setAndGetTransactionalTag(self):
    tag = "TAG-%s" % self.generateNewId()
    self.portal.Base_setTransactionalTag(tag)
    self.assertEqual(self.portal.Base_getTransactionalTag(tag), tag)

  def test_getTransactionalTagNotFound(self):
    tag = "NONEXISTENT-%s" % self.generateNewId()
    self.assertIsNone(self.portal.Base_getTransactionalTag(tag))


class TestComputeNode_invalidateIfEmpty(TestSlapOSCloudSkinsMixin):

  def _makeComputeNodeWithScope(self, scope):
    _ = self.addProject()
    compute_node = self.portal.compute_node_module.newContent(
      portal_type="Compute Node",
      title="TEST-%s" % self.generateNewId(),
      allocation_scope=scope
    )
    return compute_node

  def test_invalidateIfEmptyNoPartitions(self):
    compute_node = self._makeComputeNodeWithScope("close/forever")
    compute_node.ComputeNode_invalidateIfEmpty()
    self.tic()
    self.assertEqual(compute_node.getValidationState(), "invalidated")

  def test_invalidateIfEmptyNoInstances(self):
    compute_node = self._makeComputeNodeWithScope("close/forever")
    compute_node.newContent(
      portal_type="Compute Partition",
      title="TEST-%s" % self.generateNewId()
    )
    self.tic()
    compute_node.ComputeNode_invalidateIfEmpty()
    self.tic()
    self.assertEqual(compute_node.getValidationState(), "invalidated")

  def test_invalidateIfEmptyWithInstances(self):
    compute_node, partition = self._makeComputeNode(self.addProject())
    compute_node.edit(allocation_scope="close/forever")
    self._makeSoftwareInstance(partition, 'start_requested')
    compute_node.ComputeNode_invalidateIfEmpty()
    self.tic()
    self.assertEqual(compute_node.getValidationState(), "validated")

  def test_invalidateIfEmptyWrongScope(self):
    compute_node = self._makeComputeNodeWithScope("open")
    self.assertRaises(ValueError, compute_node.ComputeNode_invalidateIfEmpty)


class TestInstanceTree_getDefaultImageAbsoluteUrl(TestSlapOSCloudSkinsMixin):

  def test_getDefaultImageNoProduct(self):
    _, partition = self._makeComputeNode(self.addProject())
    instance_tree, _, _ = self._makeSoftwareInstance(partition)
    url = instance_tree.InstanceTree_getDefaultImageAbsoluteUrl()
    self.assertIn('gadget_slapos_panel.png', url)

  def test_getDefaultImageWithProduct(self):
    project = self.addProject()
    _ = self._makeSoftwareProduct(project)
    _, partition = self._makeComputeNode(project)
    instance_tree, _, _ = self._makeSoftwareInstance(partition)
    instance_tree.InstanceTree_getSoftwareProduct()
    url = instance_tree.InstanceTree_getDefaultImageAbsoluteUrl()
    self.assertIn('gadget_slapos_panel.png', url)


class TestInstanceTree_getSoftwareProduct(TestSlapOSCloudSkinsMixin):

  def test_getSoftwareProductMatch(self):
    project = self.addProject()
    software_product = self._makeSoftwareProduct(project)
    software_product.edit(use='trade/sale')
    release_variation = software_product.contentValues(portal_type='Software Product Release Variation')[0]
    type_variation = software_product.contentValues(portal_type='Software Product Type Variation')[0]
    type_variation.setTitle("MATCHING-TYPE-%s" % self.generateNewId())
    instance_tree, _, _ = self._makeSoftwareInstance(
      self._makeComputeNode(project)[1]
    )
    instance_tree.edit(url_string=release_variation.getUrlString(),
                       source_reference=type_variation.getTitle(),
                       follow_up_value=project)
    self.tic()
    result = instance_tree.InstanceTree_getSoftwareProduct()
    self.assertEqual(result[0], software_product)
    self.assertEqual(result[1], release_variation)
    self.assertEqual(result[2], type_variation)

  def test_getSoftwareProductNoUrl(self):
    project = self.addProject()
    instance_tree, _, _ = self._makeSoftwareInstance(
      self._makeComputeNode(project)[1]
    )
    instance_tree.edit(url_string=None)
    self.tic()
    self.assertEqual(instance_tree.InstanceTree_getSoftwareProduct(), (None, None, None))

  def test_getSoftwareProductNotFound(self):
    project = self.addProject()
    instance_tree, _, _ = self._makeSoftwareInstance(
      self._makeComputeNode(project)[1]
    )
    instance_tree.edit(url_string="http://nonexistent.example.org/software.cfg")
    self.tic()
    self.assertEqual(instance_tree.InstanceTree_getSoftwareProduct(), (None, None, None))


class TestSoftwareInstallation_getInstallationState(TestSlapOSCloudSkinsMixin):

  def _makeSoftwareInstallation(self, state):
    compute_node, _ = self._makeComputeNode(self.addProject())
    installation = self.portal.software_installation_module.newContent(
      portal_type="Software Installation",
      url_string=self.generateNewSoftwareReleaseUrl(),
      aggregate=compute_node.getRelativeUrl(),
      reference="TESTSI-%s" % self.generateNewId(),
      title="TEST-%s" % self.generateNewId(),
      follow_up_value=self.addProject()
    )
    installation.validate()
    if state == 'start_requested':
      installation.requestStart()
    elif state == 'destroy_requested':
      installation.requestStart()
      installation.requestDestroy()
    elif state == 'destroyed':
      installation.requestStart()
      installation.requestDestroy()
      installation.invalidate()
    return installation

  def test_getInstallationStateDestroyed(self):
    installation = self._makeSoftwareInstallation('destroyed')
    self.assertEqual(installation.SoftwareInstallation_getInstallationState(), 'Destroyed')

  def test_getInstallationStateStartRequested(self):
    installation = self._makeSoftwareInstallation('start_requested')
    self.assertEqual(installation.SoftwareInstallation_getInstallationState(), 'Installation requested')

  def test_getInstallationStateDestroyRequested(self):
    installation = self._makeSoftwareInstallation('destroy_requested')
    self.assertEqual(installation.SoftwareInstallation_getInstallationState(), 'Destruction requested')


class TestSoftwareInstance_bangAsSelf(TestSlapOSCloudSkinsMixin):

  def test_bangAsSelfMissingRelativeUrl(self):
    _, partition = self._makeComputeNode(self.addProject())
    _, instance, _ = self._makeSoftwareInstance(partition)
    self.assertRaises(TypeError, instance.SoftwareInstance_bangAsSelf)

  def test_bangAsSelfMissingReference(self):
    _, partition = self._makeComputeNode(self.addProject())
    _, instance, _ = self._makeSoftwareInstance(partition)
    self.assertRaises(TypeError, instance.SoftwareInstance_bangAsSelf,
                      relative_url=instance.getRelativeUrl())

  def test_bangAsSelfCallsBang(self):
    _, partition = self._makeComputeNode(self.addProject())
    _, instance, _ = self._makeSoftwareInstance(partition)
    instance.SoftwareInstance_bangAsSelf(
      relative_url=instance.getRelativeUrl(),
      reference=instance.getReference(),
      comment="Test bang"
    )


class TestSoftwareInstance_getComputePartitionIPv6(TestSlapOSCloudSkinsMixin):

  def _makeInstanceWithIPv6(self, ipv6=None):
    _, partition = self._makeComputeNode(self.addProject())
    _, instance, _ = self._makeSoftwareInstance(partition)
    if ipv6 is not None:
      partition.newContent(
        portal_type='Internet Protocol Address',
        ip_address=ipv6,
        id='ipv6_test'
      )
    return instance

  def test_getComputePartitionIPv6NoPartition(self):
    instance = self.portal.software_instance_module.newContent(
      portal_type="Software Instance",
      title="TEST-%s" % self.generateNewId(),
      reference="TESTSI-%s" % self.generateNewId()
    )
    instance.validate()
    self.assertEqual(instance.SoftwareInstance_getComputePartitionIPv6(), "")

  def test_getComputePartitionIPv6Found(self):
    instance = self._makeInstanceWithIPv6("2001:db8::1")
    self.assertEqual(instance.SoftwareInstance_getComputePartitionIPv6(), "2001:db8::1")

  def test_getComputePartitionIPv6NotFound(self):
    instance = self._makeInstanceWithIPv6("10.0.0.1")
    self.assertEqual(instance.SoftwareInstance_getComputePartitionIPv6(), "")

class TestComputeNode_getFreeComputePartitionCount(TestSlapOSCloudSkinsMixin):

  def test_getFreeComputePartitionCountAllBusy(self):
    compute_node, partition = self._makeComputeNode(self.addProject())
    self._makeSoftwareInstance(partition, 'start_requested')
    self.assertEqual(compute_node.ComputeNode_getFreeComputePartitionCount(), 0)


class TestComputeNode_getSoftwareReleaseUrlStringList(TestSlapOSCloudSkinsMixin):

  def _makeSoftwareInstallation(self, compute_node, state='start_requested', url=None):
    if url is None:
      url = self.generateNewSoftwareReleaseUrl()
    installation = self.portal.software_installation_module.newContent(
      portal_type="Software Installation",
      url_string=url,
      aggregate=compute_node.getRelativeUrl(),
      reference="TESTSI-%s" % self.generateNewId(),
      title="TEST-%s" % self.generateNewId(),
      follow_up_value=self.addProject()
    )
    installation.validate()
    if state == 'destroy_requested':
      installation.requestStart()
      installation.requestDestroy()
    elif state == 'start_requested':
      installation.requestStart()
    return installation

  def test_getSoftwareReleaseUrlStringListEmpty(self):
    compute_node, _ = self._makeComputeNode(self.addProject())
    self.assertEqual(compute_node.ComputeNode_getSoftwareReleaseUrlStringList(), [])

  def test_getSoftwareReleaseUrlStringListWithInstallations(self):
    compute_node, _ = self._makeComputeNode(self.addProject())
    url = self.generateNewSoftwareReleaseUrl()
    self._makeSoftwareInstallation(compute_node, 'start_requested', url)
    self.tic()
    result = compute_node.ComputeNode_getSoftwareReleaseUrlStringList()
    self.assertIn(url, result)

  def test_getSoftwareReleaseUrlStringListDestroyed(self):
    compute_node, _ = self._makeComputeNode(self.addProject())
    url = self.generateNewSoftwareReleaseUrl()
    self._makeSoftwareInstallation(compute_node, 'destroy_requested', url)
    result = compute_node.ComputeNode_getSoftwareReleaseUrlStringList()
    self.assertNotIn(url, result)


class TestComputePartition_getAvailableSoftwareReleaseUrlStringList(TestSlapOSCloudSkinsMixin):

  def test_getAvailableSoftwareReleaseUrlStringListFree(self):
    compute_node, partition = self._makeComputeNode(self.addProject())
    url = self.generateNewSoftwareReleaseUrl()
    installation = self.portal.software_installation_module.newContent(
      portal_type="Software Installation",
      url_string=url,
      aggregate=compute_node.getRelativeUrl(),
      reference="TESTSI-%s" % self.generateNewId(),
      title="TEST-%s" % self.generateNewId(),
      follow_up_value=self.addProject()
    )
    installation.validate()
    installation.requestStart()
    self.tic()
    result = partition.ComputePartition_getAvailableSoftwareReleaseUrlStringList()
    self.assertIn(url, result)

  def test_getAvailableSoftwareReleaseUrlStringListBusy(self):
    _, partition = self._makeComputeNode(self.addProject())
    url = self.generateNewSoftwareReleaseUrl()
    _, instance, _ = self._makeSoftwareInstance(partition, 'start_requested')
    instance.edit(url_string=url)
    self.tic()
    result = partition.ComputePartition_getAvailableSoftwareReleaseUrlStringList()
    self.assertIn(url, result)

  def test_getAvailableSoftwareReleaseUrlStringListBusyNoInstance(self):
    _, partition = self._makeComputeNode(self.addProject())
    partition.markBusy()
    self.tic()
    result = partition.ComputePartition_getAvailableSoftwareReleaseUrlStringList()
    self.assertEqual(result, ['INSTANCE NOT INDEXED YET'])

  def test_getAvailableSoftwareReleaseUrlStringListOther(self):
    _, partition = self._makeComputeNode(self.addProject())
    partition.invalidate()
    self.tic()
    result = partition.ComputePartition_getAvailableSoftwareReleaseUrlStringList()
    self.assertEqual(result, [])

