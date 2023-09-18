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

from erp5.component.test.testSlapOSPDMSkins import TestSlapOSPDMMixinSkins
from DateTime import DateTime
import transaction

class TestSlapOSPDMCreateUpgradeDecisionSkins(TestSlapOSPDMMixinSkins):

  launch_caucase = 1

  def _makeSoftwareProductCatalog(self):
    self.software_product = self._makeSoftwareProduct(self.generateNewId())
    self.previous_software_release = self._makeSoftwareRelease(self.generateNewId())
    self.new_software_release = self._makeSoftwareRelease(self.generateNewId())

    self.previous_software_release.publish()
    self.new_software_release.publish()

    self.previous_software_release.edit(
      aggregate=self.software_product.getRelativeUrl(),
      url_string=self.generateNewSoftwareReleaseUrl(),
      version='1',
      effective_date=DateTime()-1,
    )

    self.new_software_release.edit(
      aggregate=self.software_product.getRelativeUrl(),
      url_string=self.generateNewSoftwareReleaseUrl(),
      version='2',
      effective_date=DateTime(),
    )
    self.tic()

  def _installSoftwareOnTheComputeNode(self, software_release_url_list):
    for software_release in software_release_url_list:
      software_installation = self.portal.software_installation_module\
        .newContent(portal_type='Software Installation',
        url_string=software_release,
        aggregate=self.compute_node.getRelativeUrl())
      software_installation.validate()
      software_installation.requestStart()
    self.tic()

  def _createInstance(self, url_string, shared=False):
    instance_tree = self.portal.instance_tree_module\
        .template_instance_tree.Base_createCloneDocument(batch_mode=1)
    instance_tree.edit(
    )
    instance_tree.validate()
    instance_tree.edit(
        title=self.generateNewSoftwareTitle(),
        reference="TESTHS-%s" % self.generateNewId(),
        destination_section_value=self.person
    )
    request_kw = dict(
      software_release=url_string,
      software_type=self.generateNewSoftwareType(),
      instance_xml=self.generateSafeXml(),
      sla_xml=self.generateSafeXml(),
      shared=shared,
      software_title=instance_tree.getTitle(),
      state='started'
    )
    instance_tree.requestStart(**request_kw)
    instance_tree.requestInstance(**request_kw)

    instance = instance_tree.getSuccessorValue()
    self.tic()
    return instance_tree, instance

  def _makeTreeForTestSlapOSPDMCreateUpgradeDecisionSkins(self, software_release_url):
    self.instance_tree, self.instance = self._createInstance(software_release_url)
    self.shared_instance_tree, self.shared_instance = self._createInstance(software_release_url, True)
    self.instance.setAggregate(self.partition.getRelativeUrl())
    self.shared_instance.setAggregate(self.partition.getRelativeUrl())
    self.partition.markBusy()
    self.tic()

  def afterSetUp(self):
    TestSlapOSPDMMixinSkins.afterSetUp(self)
    preference =  self.portal.portal_preferences.getActiveSystemPreference()
    preference.setPreferredCloudContractEnabled(True)
    self.tic()
    self._makeComputeNode()
    self._makeSoftwareProductCatalog()
    self._installSoftwareOnTheComputeNode([
      self.previous_software_release.getUrlString(),
      self.new_software_release.getUrlString()
    ])
    self.person = self.makePerson()
    self.tic()
    self._makeTreeForTestSlapOSPDMCreateUpgradeDecisionSkins(
       self.previous_software_release.getUrlString())

  def test_InstanceTree_createUpgradeDecision_upgradeScopeConfirmation(self):
    # check upgrade decision on HS
    self.instance_tree.setUpgradeScope('manual')
    self.tic()
    upgrade_decision = self.instance_tree.InstanceTree_createUpgradeDecision()
    self.assertEqual('planned', upgrade_decision.getSimulationState())
    shared_upgrade_decision = self.shared_instance_tree.InstanceTree_createUpgradeDecision()
    self.assertEqual(None, shared_upgrade_decision)

    # simulate upgrade of the instance tree
    upgrade_decision.confirm()
    upgrade_decision.start()
    upgrade_decision.stop()
    upgrade_decision.deliver()
    self.instance_tree.edit(url_string=self.new_software_release.getUrlString())
    self.instance.edit(url_string=self.new_software_release.getUrlString())
    self.tic()

    # check upgrade decision on shared HS related to upgraded HS
    self.shared_instance_tree.setUpgradeScope('manual')

    shared_upgrade_decision = self.shared_instance_tree.InstanceTree_createUpgradeDecision()
    self.assertEqual('started', shared_upgrade_decision.getSimulationState())

  def test_InstanceTree_createUpgradeDecision_upgradeScopeAuto(self):
    # check upgrade decision on HS
    self.instance_tree.setUpgradeScope('auto')
    self.tic()
    upgrade_decision = self.instance_tree.InstanceTree_createUpgradeDecision()
    self.assertEqual('started', upgrade_decision.getSimulationState())
    shared_upgrade_decision = self.shared_instance_tree.InstanceTree_createUpgradeDecision()
    self.assertEqual(None, shared_upgrade_decision)

    # simulate upgrade of the instance tree
    upgrade_decision.stop()
    upgrade_decision.deliver()
    self.instance_tree.edit(url_string=self.new_software_release.getUrlString())
    self.instance.edit(url_string=self.new_software_release.getUrlString())
    self.tic()

    # check upgrade decision on shared HS related to upgraded HS
    self.shared_instance_tree.setUpgradeScope('auto')

    shared_upgrade_decision = self.shared_instance_tree.InstanceTree_createUpgradeDecision()
    self.assertEqual('started', shared_upgrade_decision.getSimulationState())

  def test_InstanceTree_createUpgradeDecision_upgradeScopeDisabled(self):
    # check upgrade decision on HS
    self.instance_tree.setUpgradeScope('disabled')
    self.tic()
    upgrade_decision = self.instance_tree.InstanceTree_createUpgradeDecision()
    self.assertEqual(None, upgrade_decision)
    shared_upgrade_decision = self.shared_instance_tree.InstanceTree_createUpgradeDecision()
    self.assertEqual(None, shared_upgrade_decision)


  def testInstanceTree_createUpgradeDecision_no_newer(self):
    person = self._makePerson()
    compute_node, _ = self._makeComputeNode(owner=person)
    self._makeComputePartitions(compute_node)
    software_product = self._makeSoftwareProduct()
    software_release = self._requestSoftwareRelease(
                                    software_product.getRelativeUrl())
    url_string = software_release.getUrlString()
    self._makeSoftwareInstallation(compute_node, url_string)
    self.tic()

    # Create Instance Tree
    instance_tree = self._makeFullInstanceTree(
                                    url_string, person)
    self.tic()
    
    upgrade_decision = instance_tree.InstanceTree_createUpgradeDecision()
    self.assertEqual(upgrade_decision, None)
    
    self._makeFullSoftwareInstance(instance_tree, url_string)
    self._markComputePartitionBusy(compute_node,
                                    instance_tree.getSuccessorValue())
    
    self._requestSoftwareRelease(software_product.getRelativeUrl())
    self.tic()
    
    upgrade_decision = instance_tree.InstanceTree_createUpgradeDecision()
    self.assertEqual(upgrade_decision, None)

  def testInstanceTree_createUpgradeDecision_closed_compute_node(self):
    person = self._makePerson()
    compute_node, _ = self._makeComputeNode(owner=person, allocation_scope="close/outdated")
    self._makeComputePartitions(compute_node)
    software_product = self._makeSoftwareProduct()
    software_release = self._requestSoftwareRelease(
                                    software_product.getRelativeUrl())
    url_string = software_release.getUrlString()
    
    self._makeSoftwareInstallation( compute_node, url_string)
    
    # Create Instance Tree and Software Instance
    instance_tree = self._makeFullInstanceTree(
                                    url_string, person)
    self._makeFullSoftwareInstance(instance_tree, url_string)
    self._markComputePartitionBusy(compute_node,
                                    instance_tree.getSuccessorValue())
    
    # Install the Newest software release
    software_release2 = self._requestSoftwareRelease(
                                      software_product.getRelativeUrl())
    self._makeSoftwareInstallation(compute_node,
                                    software_release2.getUrlString())
    self.tic()
    
    up_decision = instance_tree.InstanceTree_createUpgradeDecision()
    self.assertNotEqual(up_decision, None)
    self.assertEqual(up_decision.getSimulationState(), 'planned')
    
    self.assertEqual(up_decision.UpgradeDecision_getAggregateValue("Instance Tree").\
                      getReference(), instance_tree.getReference())

    self.assertEqual(software_release2.getUrlString(),
      up_decision.UpgradeDecision_getAggregateValue("Software Release").\
                              getUrlString())

  def testInstanceTree_createUpgradeDecision_create_once_transaction(self):
    person = self._makePerson()
    compute_node, _ = self._makeComputeNode(owner=person, allocation_scope="open/personal")
    self._makeComputePartitions(compute_node)
    software_product = self._makeSoftwareProduct()
    software_release = self._requestSoftwareRelease(
                                    software_product.getRelativeUrl())
    url_string = software_release.getUrlString()
    
    self._makeSoftwareInstallation( compute_node, url_string)
    
    # Create Instance Tree and Software Instance
    instance_tree = self._makeFullInstanceTree(
                                    url_string, person)
    self._makeFullSoftwareInstance(instance_tree, url_string)
    self._markComputePartitionBusy(compute_node,
                                    instance_tree.getSuccessorValue())
    
    # Install the Newest software release
    software_release2 = self._requestSoftwareRelease(
                                      software_product.getRelativeUrl())
    self._makeSoftwareInstallation(compute_node,
                                    software_release2.getUrlString())
    self.tic()
    
    up_decision = instance_tree.InstanceTree_createUpgradeDecision()
    self.assertNotEqual(up_decision, None)
    self.assertEqual(up_decision.getSimulationState(), 'planned')
    transaction.commit()
    # call a second time without tic
    up_decision = instance_tree.InstanceTree_createUpgradeDecision()
    # no new Upgrade decision created
    self.assertEqual(up_decision, None)

  def testInstanceTree_createUpgradeDecision(self):
    person = self._makePerson()
    compute_node, _ = self._makeComputeNode(owner=person)
    self._makeComputePartitions(compute_node)
    software_product = self._makeSoftwareProduct()
    software_release = self._requestSoftwareRelease(
                                    software_product.getRelativeUrl())
    url_string = software_release.getUrlString()
    
    self._makeSoftwareInstallation( compute_node, url_string)
    
    # Create Instance Tree and Software Instance
    instance_tree = self._makeFullInstanceTree(
                                    url_string, person)
    self._makeFullSoftwareInstance(instance_tree, url_string)
    self._markComputePartitionBusy(compute_node,
                                    instance_tree.getSuccessorValue())
    
    # Install the Newest software release
    software_release2 = self._requestSoftwareRelease(
                                      software_product.getRelativeUrl())
    self._makeSoftwareInstallation(compute_node,
                                    software_release2.getUrlString())
    self.tic()
    
    up_decision = instance_tree.InstanceTree_createUpgradeDecision()
    self.assertNotEqual(up_decision, None)
    self.assertEqual(up_decision.getSimulationState(), 'planned')
    
    self.assertEqual(up_decision.UpgradeDecision_getAggregateValue("Instance Tree").\
                      getReference(), instance_tree.getReference())

    self.assertEqual(software_release2.getUrlString(),
      up_decision.UpgradeDecision_getAggregateValue("Software Release").\
                              getUrlString())
    
    self.tic()
    up_decision2 = instance_tree.InstanceTree_createUpgradeDecision()
    self.assertEqual(up_decision2, None)
  
  
  def testInstanceTree_createUpgradeDecision_with_exist(self):
    person = self._makePerson()
    compute_node, _ = self._makeComputeNode(owner=person)
    self._makeComputePartitions(compute_node)
    software_product = self._makeSoftwareProduct()
    software_release = self._requestSoftwareRelease(
                                    software_product.getRelativeUrl())
    url_string = software_release.getUrlString()
    
    self._makeSoftwareInstallation( compute_node, url_string)
    
    # Create Instance Tree and Software Instance
    instance_tree = self._makeFullInstanceTree(
                                    url_string, person)
    self._makeFullSoftwareInstance(instance_tree, url_string)
    self._markComputePartitionBusy(compute_node,
                                    instance_tree.getSuccessorValue())
    
    # Install the Newest software release
    software_release2 = self._requestSoftwareRelease(
                                      software_product.getRelativeUrl())
    self._makeSoftwareInstallation(compute_node, software_release2.getUrlString())
    self.tic()
    
    up_decision = instance_tree.InstanceTree_createUpgradeDecision()
    self.assertEqual(up_decision.getSimulationState(), 'planned')
    
    # Install the another software release
    software_release3 = self._requestSoftwareRelease(
      software_product.getRelativeUrl())
    self._makeSoftwareInstallation(compute_node, software_release3.getUrlString())
    self.tic()
    
    up_decision2 = instance_tree.InstanceTree_createUpgradeDecision()
    self.assertEqual(up_decision2.getSimulationState(), 'planned')
    self.assertEqual(up_decision.getSimulationState(), 'cancelled')
    release = up_decision2.UpgradeDecision_getAggregateValue("Software Release")
    self.assertEqual(release.getUrlString(),
                                software_release3.getUrlString())

  def testInstanceTree_createUpgradeDecision_rejected(self):
    person = self._makePerson()
    compute_node, _ = self._makeComputeNode(owner=person)
    self._makeComputePartitions(compute_node)
    software_product = self._makeSoftwareProduct()
    software_release = self._requestSoftwareRelease(
                                    software_product.getRelativeUrl())
    url_string = software_release.getUrlString()
    
    self._makeSoftwareInstallation(compute_node, url_string)
    
    # Create Instance Tree and Software Instance
    instance_tree = self._makeFullInstanceTree(
                                    url_string, person)
    self._makeFullSoftwareInstance(instance_tree, url_string)
    self._markComputePartitionBusy(compute_node,
                                    instance_tree.getSuccessorValue())
    
    # Install the Newest software release
    software_release2 = self._requestSoftwareRelease(
                                      software_product.getRelativeUrl())
    self._makeSoftwareInstallation(compute_node, software_release2.getUrlString())
    self.tic()
    
    up_decision = instance_tree.InstanceTree_createUpgradeDecision()
    self.assertEqual(up_decision.getSimulationState(), 'planned')
    
    # Reject upgrade decision
    up_decision.reject()
    self.tic()
    
    in_progress = software_release2.SoftwareRelease_getUpgradeDecisionInProgress(
                                instance_tree.getUid())
    up_decision = instance_tree.InstanceTree_createUpgradeDecision()
    # There is an upgrade decision in progress
    self.assertNotEqual(in_progress, None)
    # No new upgrade decision created with software_release2
    self.assertEqual(up_decision, None)

  def testInstanceTree_createUpgradeDecision_rejected_2(self):
    person = self._makePerson()
    compute_node, _ = self._makeComputeNode(owner=person)
    self._makeComputePartitions(compute_node)
    software_product = self._makeSoftwareProduct()
    software_release = self._requestSoftwareRelease(
                                    software_product.getRelativeUrl())
    url_string = software_release.getUrlString()
    
    self._makeSoftwareInstallation(compute_node, url_string)
    
    # Create Instance Tree and Software Instance
    instance_tree = self._makeFullInstanceTree(
                                    url_string, person)
    self._makeFullSoftwareInstance(instance_tree, url_string)
    self._markComputePartitionBusy(compute_node,
                                    instance_tree.getSuccessorValue())
    
    # Install the Newest software release
    software_release2 = self._requestSoftwareRelease(
                                      software_product.getRelativeUrl())
    self._makeSoftwareInstallation(compute_node, software_release2.getUrlString())
    self.tic()
    
    up_decision = instance_tree.InstanceTree_createUpgradeDecision()
    self.assertEqual(up_decision.getSimulationState(), 'planned')
    
    # Reject upgrade decision
    up_decision.reject()
    self.tic()
    
    # Install the another software release
    software_release3 = self._requestSoftwareRelease(
                                      software_product.getRelativeUrl())
    self._makeSoftwareInstallation(compute_node, software_release3.getUrlString())
    self.tic()
    
    decision2 = instance_tree.InstanceTree_createUpgradeDecision()
    self.assertEqual(decision2.getSimulationState(), 'planned')
    self.assertEqual(up_decision.getSimulationState(), 'rejected')
    release = decision2.UpgradeDecision_getAggregateValue("Software Release")
    self.assertEqual(release.getUrlString(),
                                software_release3.getUrlString())
  
