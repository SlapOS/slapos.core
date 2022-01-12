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

from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixin, simulate
from DateTime import DateTime

class TestSlapOSPDMMixinSkins(SlapOSTestCaseMixin):
  def afterSetUp(self):
    SlapOSTestCaseMixin.afterSetUp(self)
    self.new_id = self.generateNewId()
    self.request_kw = dict(
        software_title=self.generateNewSoftwareTitle(),
        software_type=self.generateNewSoftwareType(),
        instance_xml=self.generateSafeXml(),
        sla_xml=self.generateEmptyXml(),
        shared=False,
        state="started"
    )

  def _makePerson(self):
    person_user = self.makePerson(new_id=self.new_id)
    return person_user

  def _makeComputePartitions(self, compute_node):
    for i in range(1, 5):
      id_ = 'partition%s' % (i, )
      p = compute_node.newContent(portal_type='Compute Partition',
        id=id_,
        title=id_,
        reference=id_,
        default_network_address_ip_address='ip_address_%s' % i,
        default_network_address_netmask='netmask_%s' % i)
      p.markFree()
      p.validate()
  
  def _markComputePartitionBusy(self, compute_node, software_instance):
    for partition in compute_node.contentValues(portal_type='Compute Partition'):
      if partition.getSlapState() == 'free':
        software_instance.edit(aggregate=partition.getRelativeUrl())
        partition.markBusy()
        break
  
  def _requestSoftwareRelease(self, software_product_url, effective_date=None):
    software_release = self._makeSoftwareRelease()
    if not effective_date:
      effective_date = DateTime()
    software_release.edit(
        aggregate_value=software_product_url,
        effective_date=effective_date
    )
    software_release.publish()
    return software_release
  
  def _makeCustomSoftwareRelease(self, software_product_url, software_url):
    software_release = self._makeSoftwareRelease()
    software_release.edit(
        aggregate_value=software_product_url,
        url_string=software_url
    )
    software_release.publish()
    return software_release

  def _makeSoftwareInstallation(self, compute_node, software_release_url):
    software_installation = self.portal\
      .software_installation_module.template_software_installation\
      .Base_createCloneDocument(batch_mode=1)
    new_id = self.generateNewId()
    software_installation.edit(
      url_string=software_release_url,
      aggregate=compute_node.getRelativeUrl(),
      reference='TESTSOFTINSTS-%s' % new_id,
      title='Start requested for %s' % compute_node.getUid()
    )
    software_installation.validate()
    software_installation.requestStart()

    return software_installation

  def _makeInstanceTree(self):
    instance_tree = self.portal\
      .instance_tree_module.template_instance_tree\
      .Base_createCloneDocument(batch_mode=1)
    instance_tree.validate()
    instance_tree.edit(
        title= "Test hosting sub start %s" % self.new_id,
        reference="TESTHSS-%s" % self.new_id,
    )

    return instance_tree

  def _makeSoftwareInstance(self, instance_tree, software_url):

    kw = dict(
      software_release=software_url,
      software_type=self.generateNewSoftwareType(),
      instance_xml=self.generateSafeXml(),
      sla_xml=self.generateSafeXml(),
      shared=False,
      software_title=instance_tree.getTitle(),
      state='started'
    )
    instance_tree.requestStart(**kw)
    instance_tree.requestInstance(**kw)
    
  def _makeFullInstanceTree(self, software_url="", person=None):
    if not person:
      person = self._makePerson()
    
    instance_tree = self.portal\
      .instance_tree_module.template_instance_tree\
      .Base_createCloneDocument(batch_mode=1)
    instance_tree.edit(
        title=self.request_kw['software_title'],
        reference="TESTHS-%s" % self.new_id,
        url_string=software_url,
        source_reference=self.request_kw['software_type'],
        text_content=self.request_kw['instance_xml'],
        sla_xml=self.request_kw['sla_xml'],
        root_slave=self.request_kw['shared'],
        destination_section=person.getRelativeUrl()
    )
    instance_tree.validate()
    self.portal.portal_workflow._jumpToStateFor(instance_tree, 'start_requested')

    return instance_tree

  def _makeFullSoftwareInstance(self, instance_tree, software_url):

    software_instance = self.portal.software_instance_module\
        .template_software_instance.Base_createCloneDocument(batch_mode=1)
    software_instance.edit(
        title=self.request_kw['software_title'],
        reference="TESTSI-%s" % self.generateNewId(),
        url_string=software_url,
        source_reference=self.request_kw['software_type'],
        text_content=self.request_kw['instance_xml'],
        sla_xml=self.request_kw['sla_xml'],
        specialise=instance_tree.getRelativeUrl()
    )
    instance_tree.edit(
        successor=software_instance.getRelativeUrl()
    )
    self.portal.portal_workflow._jumpToStateFor(software_instance, 'start_requested')
    software_instance.validate()

    return software_instance

  def _makeUpgradeDecision(self):
    return self.portal.\
       upgrade_decision_module.newContent(
         portal_type="Upgrade Decision",
         title="TESTUPDE-%s" % self.new_id)

  def _makeUpgradeDecisionLine(self, upgrade_decision):
    return upgrade_decision.newContent(
         portal_type="Upgrade Decision Line",
         title="TESTUPDE-%s" % self.new_id)


class TestSlapOSPDMSkins(TestSlapOSPDMMixinSkins):

  def beforeTearDown(self):
    id_list = []
    for upgrade_decision in self.portal.portal_catalog(
               portal_type="Upgrade Decision", reference="UD-TEST%"):
      id_list.append(upgrade_decision.getId())
    self.portal.upgrade_decision_module.manage_delObjects(id_list)
    self.tic()

  def test_getSortedSoftwareReleaseListFromSoftwareProduct(self):
    software_product = self._makeSoftwareProduct()
    release_list = software_product.SoftwareProduct_getSortedSoftwareReleaseList(
      software_product.getReference())
    self.assertEqual(release_list, [])

    # published software release
    software_release1 = self._makeSoftwareRelease()
    software_release1.edit(aggregate_value=software_product.getRelativeUrl(),
        url_string='http://example.org/1-%s.cfg' % self.new_id,
        effective_date=(DateTime() + 5)
    )
    software_release1.publish()
    software_release2 = self._makeSoftwareRelease()
    software_release2.edit(aggregate_value=software_product.getRelativeUrl(),
        url_string='http://example.org/2-%s.cfg' % self.new_id
    )
    software_release2.publish()
    # 1 released software release, should not appear
    software_release3 = self._makeSoftwareRelease()
    self.assertTrue(software_release3.getValidationState() == 'released')
    software_release3.edit(aggregate_value=software_product.getRelativeUrl(),
        url_string='http://example.org/3-%s.cfg' % self.new_id
    )
    self.tic()

    release_list = software_product.SoftwareProduct_getSortedSoftwareReleaseList(
      software_product.getReference())
    self.assertEqual([release.getUrlString() for release in release_list],
      ['http://example.org/2-%s.cfg' % self.new_id, 'http://example.org/1-%s.cfg' % self.new_id])

  def test_getSortedSoftwareReleaseListFromSoftwareProduct_Changed(self):
    software_product = self._makeSoftwareProduct()
    release_list = software_product.SoftwareProduct_getSortedSoftwareReleaseList(
      software_product.getReference())
    self.assertEqual(release_list, [])
    
    # 2 published software releases
    software_release2 = self._makeSoftwareRelease()
    software_release2.publish()
    software_release2.edit(aggregate_value=software_product.getRelativeUrl(),
        url_string='http://example.org/2-%s.cfg' % self.new_id,
        effective_date=(DateTime() - 2)
    )
    # Newest software release
    software_release1 = self._makeSoftwareRelease()
    software_release1.publish()
    software_release1.edit(aggregate_value=software_product.getRelativeUrl(),
        url_string='http://example.org/1-%s.cfg' % self.new_id,
        effective_date=DateTime()
    )
    self.tic()

    release_list = software_product.SoftwareProduct_getSortedSoftwareReleaseList(
      software_product.getReference())
    self.assertEqual([release.getUrlString() for release in release_list],
      ['http://example.org/1-%s.cfg' % self.new_id, 'http://example.org/2-%s.cfg' % self.new_id])
    release_list = software_product.SoftwareProduct_getSortedSoftwareReleaseList(
      software_release_url='http://example.org/1-%s.cfg' % self.new_id)
    self.assertEqual([release.getUrlString() for release in release_list],
      ['http://example.org/1-%s.cfg' % self.new_id, 'http://example.org/2-%s.cfg' % self.new_id])
  
  
  def test_InstanceTree_getNewerSofwareRelease(self):
    person = self._makePerson()
    compute_node, _ = self._makeComputeNode(owner=person)
    software_product = self._makeSoftwareProduct()
    oldest_software_url = 'http://example.org/oldest-%s.cfg' % self.new_id
    newest_software_url = 'http://example.org/newest-%s.cfg' % self.new_id
    
    self._makeCustomSoftwareRelease(
                                software_product.getRelativeUrl(),
                                oldest_software_url)
    self._makeCustomSoftwareRelease(software_product.getRelativeUrl(),
                                    newest_software_url)
    self._makeSoftwareInstallation( compute_node, oldest_software_url)
    
    instance_tree = self._makeFullInstanceTree(
                                    oldest_software_url, person)
    self.tic()
    self.assertEqual(instance_tree.InstanceTree_getNewerSofwareRelease(),
                            None)
    
    self._makeFullSoftwareInstance(instance_tree, oldest_software_url)
    self.tic()
    release = instance_tree.InstanceTree_getNewerSofwareRelease()
    self.assertEqual(release.getUrlString(), newest_software_url)

  def testInstanceTree_getUpgradableSoftwareRelease_no_installation(self):
    person = self._makePerson()
    compute_node, _ = self._makeComputeNode(owner=person)
    self._makeComputePartitions(compute_node)
    software_product = self._makeSoftwareProduct()
    oldest_software_url = 'http://example.org/oldest-%s.cfg' % self.new_id
    newest_software_url = 'http://example.org/newest-%s.cfg' % self.new_id
    self._makeCustomSoftwareRelease(
                                software_product.getRelativeUrl(),
                                oldest_software_url)
    self._makeSoftwareInstallation( compute_node, oldest_software_url)
    hs = self._makeFullInstanceTree(
                                    oldest_software_url, person)
    self.tic()
    self.assertEqual(hs.InstanceTree_getUpgradableSoftwareRelease(),
                      None)
    
    self._makeFullSoftwareInstance(hs, oldest_software_url)
    self._markComputePartitionBusy(compute_node, hs.getSuccessorValue())
    self._makeCustomSoftwareRelease(software_product.getRelativeUrl(),
                                    newest_software_url)
    self.tic()
    self.assertEqual(hs.InstanceTree_getUpgradableSoftwareRelease(),
                      None)
  
  def testInstanceTree_getUpgradableSoftwareRelease(self):
    person = self._makePerson()
    compute_node, _ = self._makeComputeNode(owner=person)
    self._makeComputePartitions(compute_node)
    software_product = self._makeSoftwareProduct()
    oldest_software_url = 'http://example.org/oldest-%s.cfg' % self.new_id
    newest_software_url = 'http://example.org/newest-%s.cfg' % self.new_id
    self._makeCustomSoftwareRelease(
                                software_product.getRelativeUrl(),
                                oldest_software_url)
    self._makeSoftwareInstallation( compute_node, oldest_software_url)
    hs = self._makeFullInstanceTree(
                                    oldest_software_url, person)
    
    self._makeFullSoftwareInstance(hs, oldest_software_url)
    self._markComputePartitionBusy(compute_node, hs.getSuccessorValue())
    self._makeCustomSoftwareRelease(software_product.getRelativeUrl(),
                                    newest_software_url)
    self._makeSoftwareInstallation(compute_node,
                                    newest_software_url)
    # software_release should be ignored!
    software_release = self._makeSoftwareRelease()
    self._makeSoftwareInstallation(compute_node, software_release.getUrlString())
    self.tic()
    release = hs.InstanceTree_getUpgradableSoftwareRelease()
    self.assertEqual(release.getUrlString(), newest_software_url)
    
    self.portal.portal_workflow._jumpToStateFor(hs, 'destroy_requested')
    self.tic()
    self.assertEqual(hs.InstanceTree_getUpgradableSoftwareRelease(),
                      None)
                      

  def testUpgradeDecision_getComputeNode(self):
    compute_node, _ = self._makeComputeNode()
    upgrade_decision = self._makeUpgradeDecision()

    upgrade_decision_line = self._makeUpgradeDecisionLine(upgrade_decision)
    upgrade_decision_line.setAggregateValue(compute_node)

    found_compute_node = upgrade_decision.UpgradeDecision_getAggregateValue("Compute Node")
    self.assertEqual(compute_node.getRelativeUrl(),
                      found_compute_node.getRelativeUrl())

  def testUpgradeDecision_getComputeNode_2_lines(self):
    compute_node, _ = self._makeComputeNode()
    upgrade_decision = self._makeUpgradeDecision()

    upgrade_decision_line = self._makeUpgradeDecisionLine(upgrade_decision)
    upgrade_decision_line.setAggregateValue(compute_node)

    upgrade_decision_line = self._makeUpgradeDecisionLine(upgrade_decision)

    found_compute_node = upgrade_decision.UpgradeDecision_getAggregateValue("Compute Node")
    self.assertEqual(compute_node.getRelativeUrl(),
                      found_compute_node.getRelativeUrl())

  def testUpgradeDecision_getComputeNode_2_compute_node(self):
    compute_node, _ = self._makeComputeNode()
    upgrade_decision = self._makeUpgradeDecision()

    upgrade_decision_line = self._makeUpgradeDecisionLine(upgrade_decision)
    upgrade_decision_line.setAggregateValue(compute_node)

    upgrade_decision_line = self._makeUpgradeDecisionLine(upgrade_decision)
    upgrade_decision_line.setAggregateValue(compute_node)

    self.assertRaises(ValueError, upgrade_decision.UpgradeDecision_getAggregateValue,
      document_portal_type="Compute Node")

  def testUpgradeDecision_getComputeNode_O_compute_node(self):
    upgrade_decision = self._makeUpgradeDecision()
    self._makeUpgradeDecisionLine(upgrade_decision)

    found_compute_node = upgrade_decision.UpgradeDecision_getAggregateValue("Compute Node")
    self.assertEqual(None, found_compute_node)


  def testUpgradeDecision_getInstanceTree(self):
    instance_tree = self._makeInstanceTree()
    upgrade_decision = self._makeUpgradeDecision()

    upgrade_decision_line = self._makeUpgradeDecisionLine(upgrade_decision)
    upgrade_decision_line.setAggregateValue(instance_tree)

    found_instance_tree = upgrade_decision.UpgradeDecision_getAggregateValue("Instance Tree")
    self.assertEqual(instance_tree.getRelativeUrl(),
                      found_instance_tree.getRelativeUrl())


  def testUpgradeDecision_getInstanceTree_2_lines(self):
    instance_tree = self._makeInstanceTree()
    upgrade_decision = self._makeUpgradeDecision()

    upgrade_decision_line = self._makeUpgradeDecisionLine(upgrade_decision)
    upgrade_decision_line.setAggregateValue(instance_tree)

    upgrade_decision_line = self._makeUpgradeDecisionLine(upgrade_decision)

    found_instance_tree = upgrade_decision.UpgradeDecision_getAggregateValue("Instance Tree")
    self.assertEqual(instance_tree.getRelativeUrl(),
                      found_instance_tree.getRelativeUrl())


  def testUpgradeDecision_getInstanceTree_2_hosting(self):
    instance_tree = self._makeInstanceTree()
    upgrade_decision = self._makeUpgradeDecision()

    upgrade_decision_line = self._makeUpgradeDecisionLine(upgrade_decision)
    upgrade_decision_line.setAggregateValue(instance_tree)

    upgrade_decision_line = self._makeUpgradeDecisionLine(upgrade_decision)
    upgrade_decision_line.setAggregateValue(instance_tree)

    self.assertRaises(ValueError, upgrade_decision.UpgradeDecision_getAggregateValue,
      document_portal_type="Instance Tree")

  def testUpgradeDecision_getInstanceTree_O_hosting(self):
    upgrade_decision = self._makeUpgradeDecision()
    self._makeUpgradeDecisionLine(upgrade_decision)

    found_instance_tree = upgrade_decision.UpgradeDecision_getAggregateValue("Instance Tree")
    self.assertEqual(None, found_instance_tree)

     
  def testUpgradeDecision_getSoftwareRelease(self):
    software_release = self._makeSoftwareRelease()
    upgrade_decision = self._makeUpgradeDecision()

    upgrade_decision_line = self._makeUpgradeDecisionLine(upgrade_decision)
    upgrade_decision_line.setAggregateValue(software_release)

    found_software_release = upgrade_decision.UpgradeDecision_getSoftwareRelease()
    self.assertEqual(software_release.getRelativeUrl(),
                      found_software_release.getRelativeUrl())

  def testUpgradeDecision_getSoftwareRelease_2_lines(self):
    software_release = self._makeSoftwareRelease()
    upgrade_decision = self._makeUpgradeDecision()

    upgrade_decision_line = self._makeUpgradeDecisionLine(upgrade_decision)
    upgrade_decision_line.setAggregateValue(software_release)

    upgrade_decision_line = self._makeUpgradeDecisionLine(upgrade_decision)

    found_software_release = upgrade_decision.UpgradeDecision_getSoftwareRelease()
    self.assertEqual(software_release.getRelativeUrl(),
                      found_software_release.getRelativeUrl())

  def testUpgradeDecision_getSoftwareRelease_2_sr(self):
    software_release = self._makeSoftwareRelease()
    upgrade_decision = self._makeUpgradeDecision()

    upgrade_decision_line = self._makeUpgradeDecisionLine(upgrade_decision)
    upgrade_decision_line.setAggregateValue(software_release)

    upgrade_decision_line = self._makeUpgradeDecisionLine(upgrade_decision)
    upgrade_decision_line.setAggregateValue(software_release)

    self.assertRaises(ValueError, upgrade_decision.UpgradeDecision_getSoftwareRelease)

  def testUpgradeDecision_getSoftwareRelease_O_sr(self):
    upgrade_decision = self._makeUpgradeDecision()
    self._makeUpgradeDecisionLine(upgrade_decision)

    found_software_release = upgrade_decision.UpgradeDecision_getSoftwareRelease()
    self.assertEqual(None, found_software_release)

  @simulate('InstanceTree_isUpgradePossible',
            'software_release_url', 'return 1')
  def testUpgradeDecision_upgradeInstanceTree(self):
    person = self._makePerson()
    instance_tree = self._makeInstanceTree()
    instance_tree.edit(
          destination_section_value = person.getRelativeUrl())

    self._makeSoftwareInstance(instance_tree,
                               instance_tree.getUrlString())
   
    software_release = self._makeSoftwareRelease()
    upgrade_decision = self._makeUpgradeDecision()
    upgrade_decision_line = self._makeUpgradeDecisionLine(upgrade_decision)
    upgrade_decision_line.setAggregateValueList(
       [software_release, instance_tree])
    self.tic()
   
    slap_state = instance_tree.getSlapState()
    
    self.assertFalse(upgrade_decision.UpgradeDecision_upgradeInstanceTree())
    self.assertNotEqual(software_release.getUrlString(),
                     instance_tree.getUrlString())

    upgrade_decision.confirm()
    upgrade_decision.start()

    # Check that url_string change, but slap state doesn't
    self.assertNotEqual(software_release.getUrlString(),
                     instance_tree.getUrlString())

    self.assertTrue(upgrade_decision.UpgradeDecision_upgradeInstanceTree())
    self.assertEqual(software_release.getUrlString(),
                     instance_tree.getUrlString())

    self.assertEqual(slap_state, instance_tree.getSlapState())
    self.assertEqual('stopped', upgrade_decision.getSimulationState())

  @simulate('InstanceTree_isUpgradePossible',
            'software_release_url', 'return 1')
  def testUpgradeDecision_processUpgradeeInstanceTree(self):
    person = self._makePerson()
    instance_tree = self._makeInstanceTree()
    instance_tree.edit(
          destination_section_value = person.getRelativeUrl())

    self._makeSoftwareInstance(instance_tree,
                               instance_tree.getUrlString())
   
    software_release = self._makeSoftwareRelease()
    upgrade_decision = self._makeUpgradeDecision()
    upgrade_decision_line = self._makeUpgradeDecisionLine(upgrade_decision)
    upgrade_decision_line.setAggregateValueList(
       [software_release, instance_tree])
    self.tic()
   
    slap_state = instance_tree.getSlapState()
    
    self.assertFalse(upgrade_decision.UpgradeDecision_processUpgrade())
    self.assertNotEqual(software_release.getUrlString(),
                     instance_tree.getUrlString())

    upgrade_decision.confirm()
    upgrade_decision.start()

    # Check that url_string change, but slap state doesn't
    self.assertNotEqual(software_release.getUrlString(),
                     instance_tree.getUrlString())

    self.assertTrue(upgrade_decision.UpgradeDecision_processUpgrade())
    self.assertEqual(software_release.getUrlString(),
                     instance_tree.getUrlString())

    self.assertEqual(slap_state, instance_tree.getSlapState())
    self.assertEqual('stopped', upgrade_decision.getSimulationState())


  def testUpgradeDecision_upgradeInstanceTree_no_software_release(self):

    person = self._makePerson()
    instance_tree = self._makeInstanceTree()
    instance_tree.edit(
          destination_section_value = person.getRelativeUrl())

    self._makeSoftwareInstance(instance_tree,
                               instance_tree.getUrlString())
   
    upgrade_decision = self._makeUpgradeDecision()
    upgrade_decision_line = self._makeUpgradeDecisionLine(upgrade_decision)
    upgrade_decision_line.setAggregateValueList([instance_tree])
    self.tic()
   
    upgrade_decision.confirm()
    upgrade_decision.start()

    self.assertFalse(upgrade_decision.UpgradeDecision_upgradeInstanceTree())
    self.assertEqual('started', upgrade_decision.getSimulationState())

  def testUpgradeDecision_upgradeInstanceTree_no_hosting_subscripion(self):

    software_release = self._makeSoftwareRelease()
    upgrade_decision = self._makeUpgradeDecision()
    upgrade_decision_line = self._makeUpgradeDecisionLine(upgrade_decision)
    upgrade_decision_line.setAggregateValueList([software_release])
    self.tic()
    
    upgrade_decision.confirm()
    upgrade_decision.start()

    self.assertFalse(upgrade_decision.UpgradeDecision_upgradeInstanceTree())
    self.assertEqual('started', upgrade_decision.getSimulationState())
    
  def testUpgradeDecision_upgradeComputeNode_no_software_release(self):

    person = self._makePerson()
    compute_node, _ = self._makeComputeNode(owner=person)

    upgrade_decision = self._makeUpgradeDecision()
    upgrade_decision_line = self._makeUpgradeDecisionLine(upgrade_decision)
    upgrade_decision_line.setAggregateValueList([compute_node])
    self.tic()
   
    upgrade_decision.confirm()
    upgrade_decision.start()

    self.assertFalse(upgrade_decision.UpgradeDecision_upgradeComputeNode())
    self.assertEqual('started', upgrade_decision.getSimulationState())


  def testUpgradeDecision_upgradeComputeNode_no_hosting_subscripion(self):

    software_release = self._makeSoftwareRelease()
    upgrade_decision = self._makeUpgradeDecision()
    upgrade_decision_line = self._makeUpgradeDecisionLine(upgrade_decision)
    upgrade_decision_line.setAggregateValueList([software_release])
    self.tic()
    
    upgrade_decision.confirm()
    upgrade_decision.start()

    self.assertFalse(upgrade_decision.UpgradeDecision_upgradeComputeNode())
    self.assertEqual('started', upgrade_decision.getSimulationState())
    
  def testUpgradeDecision_upgradeComputeNode(self):
    self._makePerson()
    compute_node, _ = self._makeComputeNode()
    software_release = self._makeSoftwareRelease()
    upgrade_decision = self._makeUpgradeDecision()
    upgrade_decision_line = self._makeUpgradeDecisionLine(upgrade_decision)
    upgrade_decision_line.setAggregateValueList([software_release, compute_node])
    url = software_release.getUrlString()
    
    self.tic()

    self.assertFalse(upgrade_decision.UpgradeDecision_upgradeComputeNode())

    upgrade_decision.confirm()
    upgrade_decision.start()

    self.assertTrue(upgrade_decision.UpgradeDecision_upgradeComputeNode())
    self.tic()
    
    software_installation = compute_node.getAggregateRelatedValue(
            portal_type='Software Installation')
    self.assertEqual('start_requested', software_installation.getSlapState())
    self.assertEqual(url, software_installation.getUrlString())
    self.assertEqual('validated', software_installation.getValidationState())
    self.assertEqual('stopped', upgrade_decision.getSimulationState())


  def testUpgradeDecision_processUpgradeComputeNode(self):
    self._makePerson()
    compute_node, _ = self._makeComputeNode()
    software_release = self._makeSoftwareRelease()
    upgrade_decision = self._makeUpgradeDecision()
    upgrade_decision_line = self._makeUpgradeDecisionLine(upgrade_decision)
    upgrade_decision_line.setAggregateValueList([software_release, compute_node])
    url = software_release.getUrlString()
    
    self.tic()

    self.assertFalse(upgrade_decision.UpgradeDecision_processUpgrade())

    upgrade_decision.confirm()
    upgrade_decision.start()

    self.assertTrue(upgrade_decision.UpgradeDecision_processUpgrade())
    self.tic()
    
    software_installation = compute_node.getAggregateRelatedValue(
            portal_type='Software Installation')
    self.assertEqual('start_requested', software_installation.getSlapState())
    self.assertEqual(url, software_installation.getUrlString())
    self.assertEqual('validated', software_installation.getValidationState())
    self.assertEqual('stopped', upgrade_decision.getSimulationState())


  def testSoftwareRelease_createUpgradeDecision_compute_node(self):
    person = self._makePerson()
    compute_node, _ = self._makeComputeNode(owner=person)
    software_release = self._makeSoftwareRelease()
    
    upgrade_decision = software_release.SoftwareRelease_createUpgradeDecision(
          source_url=compute_node.getRelativeUrl(),
          title="TEST-SRUPDE-%s" % self.new_id)
    self.tic()
    
    self.assertEqual(upgrade_decision.getSimulationState(), 'draft')
    self.assertEqual(upgrade_decision.getDestinationSection(),
                       person.getRelativeUrl())
    
    decision_line = upgrade_decision.contentValues(
                    portal_type='Upgrade Decision Line')[0]
    
    self.assertEqual(decision_line.getTitle(),
                        'Request decision upgrade for %s on Compute Node %s' % (
                        software_release.getTitle(), compute_node.getReference())
                    )
    self.assertEqual(decision_line.getAggregate(portal_type='Compute Node'),
                      compute_node.getRelativeUrl())
    self.assertEqual(decision_line.getAggregate(portal_type='Software Release'),
                      software_release.getRelativeUrl())
  
  
  def testSoftwareRelease_createUpgradeDecision_hostingSubscription(self):
    person = self._makePerson()
    instance_tree = self._makeInstanceTree()
    instance_tree.edit(
          destination_section_value = person.getRelativeUrl())
    software_release = self._makeSoftwareRelease()
    
    upgrade_decision = software_release.SoftwareRelease_createUpgradeDecision(
          source_url=instance_tree.getRelativeUrl(),
          title="TEST-SRUPDE-%s" % self.new_id)
    self.tic()
    
    self.assertEqual(upgrade_decision.getSimulationState(), 'draft')
    self.assertEqual(upgrade_decision.getDestinationSection(),
                       person.getRelativeUrl())
    
    decision_line = upgrade_decision.contentValues(
                    portal_type='Upgrade Decision Line')[0]
                    
    self.assertEqual(decision_line.getAggregate(portal_type='Instance Tree'),
                      instance_tree.getRelativeUrl())
    self.assertEqual(decision_line.getAggregate(portal_type='Software Release'),
                      software_release.getRelativeUrl())
  
  
  def testSoftwareRelease_getUpgradeDecisionInProgress(self):
    compute_node, _ = self._makeComputeNode()
    software_product = self._makeSoftwareProduct()
    software_release = self._requestSoftwareRelease(
                                    software_product.getRelativeUrl())
    upgrade_decision = self._makeUpgradeDecision()
    upgrade_decision_line = self._makeUpgradeDecisionLine(upgrade_decision)
    upgrade_decision_line.setAggregateValueList([software_release, compute_node])
    software_release2 = self._makeSoftwareRelease()
    upgrade_decision.confirm()
    reference = upgrade_decision.getReference()
    
    self.tic()
    
    in_progress = software_release.SoftwareRelease_getUpgradeDecisionInProgress(
                                compute_node.getUid())
    self.assertEqual(in_progress.getReference(), reference)
    
    in_progress = software_release.SoftwareRelease_getUpgradeDecisionInProgress(
                                software_release.getUid())
    self.assertEqual(in_progress.getReference(), reference)
    
    in_progress = software_release2.SoftwareRelease_getUpgradeDecisionInProgress(
                                compute_node.getUid())
    self.assertEqual(in_progress, None)
  
  def testSoftwareRelease_getUpgradeDecisionInProgress_cancelled(self):
    compute_node, _ = self._makeComputeNode()
    software_product = self._makeSoftwareProduct()
    software_release = self._requestSoftwareRelease(
                                    software_product.getRelativeUrl())
    upgrade_decision = self._makeUpgradeDecision()
    upgrade_decision_line = self._makeUpgradeDecisionLine(upgrade_decision)
    upgrade_decision_line.setAggregateValueList([software_release, compute_node])
    upgrade_decision.confirm()
    upgrade_decision.cancel()
    
    self.tic()
    in_progress = software_release.SoftwareRelease_getUpgradeDecisionInProgress(
                                compute_node.getUid())
    self.assertEqual(in_progress, None)
    
    upgrade_decision2 = self._makeUpgradeDecision()
    upgrade_decision_line2 = self._makeUpgradeDecisionLine(upgrade_decision2)
    upgrade_decision_line2.setAggregateValueList([software_release, compute_node])
    upgrade_decision2.confirm()
    upgrade_decision2.start()
    self.tic()
    
    in_progress = software_release.SoftwareRelease_getUpgradeDecisionInProgress(
                                compute_node.getUid())
    self.assertEqual(in_progress.getReference(), upgrade_decision2.getReference())

  def testSoftwareRelease_getUpgradeDecisionInProgress_rejected(self):
    compute_node, _ = self._makeComputeNode()
    software_product = self._makeSoftwareProduct()
    software_release = self._requestSoftwareRelease(
                                    software_product.getRelativeUrl())
    upgrade_decision = self._makeUpgradeDecision()
    upgrade_decision_line = self._makeUpgradeDecisionLine(upgrade_decision)
    upgrade_decision_line.setAggregateValueList([software_release, compute_node])
    upgrade_decision.confirm()
    upgrade_decision.reject()
    
    self.tic()
    in_progress = software_release.SoftwareRelease_getUpgradeDecisionInProgress(
                                compute_node.getUid())
    # XXX - in_progress is the rejected upgrade decision
    self.assertEqual(in_progress.getReference(), upgrade_decision.getReference())
    
    new_release = self._requestSoftwareRelease(
                                    software_product.getRelativeUrl())
    self.tic()
    
    in_progress = new_release.SoftwareRelease_getUpgradeDecisionInProgress(
                                compute_node.getUid())
    self.assertEqual(in_progress, None)
    
    upgrade_decision2 = self._makeUpgradeDecision()
    upgrade_decision_line2 = self._makeUpgradeDecisionLine(upgrade_decision2)
    upgrade_decision_line2.setAggregateValueList([new_release, compute_node])
    upgrade_decision2.confirm()
    upgrade_decision2.start()
    self.tic()
    
    in_progress = new_release.SoftwareRelease_getUpgradeDecisionInProgress(
                                compute_node.getUid())
    self.assertEqual(in_progress.getReference(), upgrade_decision2.getReference())
  
  def testSoftwareRelease_getUpgradeDecisionInProgress_hosting_subs(self):
    person = self._makePerson()
    instance_tree = self._makeInstanceTree()
    instance_tree.edit(
          destination_section_value = person.getRelativeUrl())
    software_product = self._makeSoftwareProduct()
    software_release = self._requestSoftwareRelease(
                                    software_product.getRelativeUrl())
    upgrade_decision = self._makeUpgradeDecision()
    upgrade_decision_line = self._makeUpgradeDecisionLine(upgrade_decision)
    upgrade_decision_line.setAggregateValueList([software_release,
                                                      instance_tree])
    upgrade_decision.confirm()
    reference = upgrade_decision.getReference()
    self.tic()
    
    in_progress = software_release.SoftwareRelease_getUpgradeDecisionInProgress(
                                instance_tree.getUid())
    self.assertEqual(in_progress.getReference(), reference)
    
    upgrade_decision.cancel()
    self.tic()
    
    in_progress = software_release.SoftwareRelease_getUpgradeDecisionInProgress(
                                instance_tree.getUid())
    self.assertEqual(in_progress, None)
  
  
  def testSoftwareRelease_getUpgradeDecisionInProgress_software_product(self):
    compute_node, _ = self._makeComputeNode()
    software_product = self._makeSoftwareProduct()
    software_release = self._requestSoftwareRelease(
                                    software_product.getRelativeUrl())
    software_release2 = self._requestSoftwareRelease(
                                      software_product.getRelativeUrl())
    software_release3 = self._makeSoftwareRelease()
    upgrade_decision = self._makeUpgradeDecision()
    upgrade_decision_line = self._makeUpgradeDecisionLine(upgrade_decision)
    upgrade_decision_line.setAggregateValueList([software_release, compute_node])
    upgrade_decision.confirm()
    reference = upgrade_decision.getReference()
    
    self.tic()
    
    in_progress = software_release.SoftwareRelease_getUpgradeDecisionInProgress(
                                compute_node.getUid())
    self.assertEqual(in_progress.getReference(), reference)
    
    in_progress = software_release2.SoftwareRelease_getUpgradeDecisionInProgress(
                                compute_node.getUid())
    self.assertEqual(in_progress.getReference(), reference)
    
    in_progress = software_release3.SoftwareRelease_getUpgradeDecisionInProgress(
                                compute_node.getUid())
    self.assertEqual(in_progress, None)
  
  
  def testSoftwareRelease_getUpgradeDecisionInProgress_software_product_hs(self):
    person = self._makePerson()
    instance_tree = self._makeInstanceTree()
    instance_tree.edit(
          destination_section_value = person.getRelativeUrl())
    software_product = self._makeSoftwareProduct()
    software_release = self._requestSoftwareRelease(
                                    software_product.getRelativeUrl())
    software_release2 = self._requestSoftwareRelease(
                                      software_product.getRelativeUrl())
    software_release3 = self._makeSoftwareRelease()
    upgrade_decision = self._makeUpgradeDecision()
    upgrade_decision_line = self._makeUpgradeDecisionLine(upgrade_decision)
    upgrade_decision_line.setAggregateValueList([software_release,
                                                      instance_tree])
    upgrade_decision.confirm()
    reference = upgrade_decision.getReference()
    reference = upgrade_decision.getReference()
    
    self.tic()
    
    in_progress = software_release.SoftwareRelease_getUpgradeDecisionInProgress(
                                instance_tree.getUid())
    self.assertEqual(in_progress.getReference(), reference)
    
    in_progress = software_release2.SoftwareRelease_getUpgradeDecisionInProgress(
                                instance_tree.getUid())
    self.assertEqual(in_progress.getReference(), reference)
    
    in_progress = software_release3.SoftwareRelease_getUpgradeDecisionInProgress(
                                instance_tree.getUid())
    self.assertEqual(in_progress, None)
  
  
  def testUpgradeDecision_tryToCancel(self):
    compute_node, _ = self._makeComputeNode()
    software_release = self._makeSoftwareRelease()
    software_release2 = self._makeSoftwareRelease()
    upgrade_decision = self._makeUpgradeDecision()
    upgrade_decision_line = self._makeUpgradeDecisionLine(upgrade_decision)
    upgrade_decision_line.setAggregateValueList([software_release, compute_node])
    upgrade_decision.confirm()
    
    upgrade_decision2 = self._makeUpgradeDecision()
    upgrade_decision_line2 = self._makeUpgradeDecisionLine(upgrade_decision2)
    upgrade_decision_line2.setAggregateValueList([software_release, compute_node])
    upgrade_decision2.confirm()
    upgrade_decision2.start()
    
    url = software_release.getUrlString()
    url2 = software_release2.getUrlString()
    
    # Cancel is not possible with the same url_string
    self.assertEqual(upgrade_decision.UpgradeDecision_tryToCancel(url), False)
    self.assertEqual(upgrade_decision.UpgradeDecision_tryToCancel(url2), True)
    self.assertEqual(upgrade_decision.getSimulationState(), 'cancelled')
    
    # Cancel is no longer possible
    self.assertEqual(upgrade_decision2.UpgradeDecision_tryToCancel(url), False)
    self.assertEqual(upgrade_decision2.UpgradeDecision_tryToCancel(url2), False)
    self.assertEqual(upgrade_decision2.getSimulationState(), 'started')

  def testUpgradeDecision_tryToCancel_withRejected(self):
    compute_node, _ = self._makeComputeNode()
    software_release = self._makeSoftwareRelease()
    software_release2 = self._makeSoftwareRelease()
    upgrade_decision = self._makeUpgradeDecision()
    upgrade_decision_line = self._makeUpgradeDecisionLine(upgrade_decision)
    upgrade_decision_line.setAggregateValueList([software_release, compute_node])
    upgrade_decision.confirm()
    upgrade_decision.reject()
    
    url = software_release.getUrlString()
    url2 = software_release2.getUrlString()
    
    # Try to cancel rejected UD with the same sr will return False
    self.assertEqual(upgrade_decision.UpgradeDecision_tryToCancel(url), False)
    self.assertEqual(upgrade_decision.getSimulationState(), 'rejected')
    # Try to cancel rejected UD will return True with url2
    self.assertEqual(upgrade_decision.UpgradeDecision_tryToCancel(url2), True)
    self.assertEqual(upgrade_decision.getSimulationState(), 'rejected')
    
  def testComputeNode_checkAndCreateUpgradeDecision_auto(self):
    person = self._makePerson()
    compute_node, _ = self._makeComputeNode(owner=person,
                  allocation_scope="open/public")
    compute_node.edit(upgrade_scope="auto")
    software_product = self._makeSoftwareProduct()
    software_release = self._requestSoftwareRelease(
                                    software_product.getRelativeUrl())
    self._makeSoftwareInstallation(
                              compute_node, software_release.getUrlString())
    self.tic()
    upgrade_decision = compute_node.ComputeNode_checkAndCreateUpgradeDecision()
    self.assertEqual(len(upgrade_decision), 0)
    
    software_release2 = self._requestSoftwareRelease(
                                      software_product.getRelativeUrl())
    # Should be ignored, Publication Date is for tomorrow
    self._requestSoftwareRelease(software_product.getRelativeUrl(),
                                 (DateTime() + 1))
    self.tic()
    
    upgrade_decision = compute_node.ComputeNode_checkAndCreateUpgradeDecision()
    self.assertEqual(len(upgrade_decision), 1)
    self.assertEqual(upgrade_decision[0].getSimulationState(), 'started')
    
    compute_node_aggregate = upgrade_decision[0].UpgradeDecision_getAggregateValue("Compute Node")()
    self.assertEqual(compute_node_aggregate.getReference(),
                      compute_node.getReference())
    release = upgrade_decision[0].UpgradeDecision_getSoftwareRelease()
    self.assertEqual(release.getUrlString(),
                                software_release2.getUrlString())
    self.tic()
    upgrade_decision2 = compute_node.ComputeNode_checkAndCreateUpgradeDecision()
    self.assertEqual(len(upgrade_decision2), 0)
  
  def testComputeNode_checkAndCreateUpgradeDecision_ask_confirmation_with_exist(self):
    person = self._makePerson()
    compute_node, _ = self._makeComputeNode(owner=person, 
            allocation_scope="open/personal")
    compute_node.edit(upgrade_scope="ask_confirmation")
    software_product = self._makeSoftwareProduct()
    software_release = self._requestSoftwareRelease(
                                    software_product.getRelativeUrl())
    self._makeSoftwareInstallation(
                              compute_node, software_release.getUrlString())
    self._requestSoftwareRelease(software_product.getRelativeUrl())
    self.tic()
    
    self.assertEqual(compute_node.getUpgradeScope(), "ask_confirmation")
    upgrade_decision = compute_node.ComputeNode_checkAndCreateUpgradeDecision()[0]
    self.assertEqual(upgrade_decision.getSimulationState(), 'planned')
    
    software_release3 = self._requestSoftwareRelease(
                                      software_product.getRelativeUrl())
    self.tic()
    
    upgrade_decision2 = compute_node.ComputeNode_checkAndCreateUpgradeDecision()[0]
    
    self.assertEqual(upgrade_decision.getSimulationState(), 'cancelled')
    self.assertEqual(upgrade_decision2.getSimulationState(), 'planned')
    release = upgrade_decision2.UpgradeDecision_getSoftwareRelease()
    self.assertEqual(release.getUrlString(),
                                software_release3.getUrlString())
  
  def testComputeNode_checkAndCreateUpgradeDecision_auto_with_exist(self):
    person = self._makePerson()
    compute_node, _ = self._makeComputeNode(owner=person,
                  allocation_scope="open/public")
    compute_node.edit(upgrade_scope="auto")
    software_product = self._makeSoftwareProduct()
    software_release = self._requestSoftwareRelease(
                                    software_product.getRelativeUrl())
    self._makeSoftwareInstallation(compute_node, software_release.getUrlString())
    self._requestSoftwareRelease(software_product.getRelativeUrl())
    self.tic()
    
    upgrade_decision = compute_node.ComputeNode_checkAndCreateUpgradeDecision()[0]
    self.assertEqual(upgrade_decision.getSimulationState(), 'started')
    
    self._requestSoftwareRelease(software_product.getRelativeUrl())
    self.tic()
    
    upgrade_decision2 = compute_node.ComputeNode_checkAndCreateUpgradeDecision()
    
    self.assertEqual(len(upgrade_decision2), 0)
    self.assertEqual(upgrade_decision.getSimulationState(), 'started')

  
  def testBase_acceptUpgradeDecision_no_reference(self):
    self._makeUpgradeDecision()
    self.assertRaises(ValueError, self.portal.Base_acceptUpgradeDecision, None)
    
  def testBase_acceptUpgradeDecision_duplicated_reference(self):
    upgrade_decision = self._makeUpgradeDecision()
    upgrade_decision.setReference("UD-TESTBADREFERENCE")
    upgrade_decision = self._makeUpgradeDecision()
    upgrade_decision.setReference("UD-TESTBADREFERENCE")
    self.tic()
    self.assertRaises(ValueError, self.portal.Base_acceptUpgradeDecision, None)

  def testBase_acceptUpgradeDecision_no_upgrade_decision(self):
    redirect_url = self.portal.Base_acceptUpgradeDecision('UD-UNEXISTING')
    self.assertTrue(redirect_url.endswith(
      "?portal_status_message=Unable%20to%20find%20the%20Upgrade%20Decision."), 
      "%s contains the wrong message" %  redirect_url)
     
  def testBase_acceptUpgradeDecision_draft_upgrade_decision(self):
    upgrade_decision = self._makeUpgradeDecision()
    upgrade_decision.setReference("UD-TESTDRAFT")
    self.tic()
    redirect_url = self.portal.Base_acceptUpgradeDecision('UD-TESTDRAFT')
    self.assertTrue(redirect_url.endswith(
      "?portal_status_message=Sorry%2C%20the%20upgrade%20is%20not%20possible%20yet%21"), 
      "%s contains the wrong message" %  redirect_url)

  def testBase_acceptUpgradeDecision_planned_upgrade_decision(self):
    upgrade_decision = self._makeUpgradeDecision()
    upgrade_decision.setReference("UD-TESTPLANNED")
    upgrade_decision.plan()
    self.tic()
    redirect_url = self.portal.Base_acceptUpgradeDecision('UD-TESTPLANNED')
    self.assertTrue(redirect_url.endswith(
      "?portal_status_message=Sorry%2C%20the%20upgrade%20is%20not%20possible%20yet%21"), 
      "%s contains the wrong message" %  redirect_url)

  def testBase_acceptUpgradeDecision_confirmed_upgrade_decision(self):
    upgrade_decision = self._makeUpgradeDecision()
    upgrade_decision.setReference("UD-TESTCONFIRMED")
    upgrade_decision.confirm()
    self.tic()
    redirect_url = self.portal.Base_acceptUpgradeDecision('UD-TESTCONFIRMED')
    self.assertTrue(redirect_url.endswith(
      "?portal_status_message=This%20Upgrade%20Decision%20has%20been%20"\
      "requested%2C%20it%20will%20be%20processed%20in%20few%20minutes."), 
      "%s contains the wrong message" %  redirect_url)
    self.assertEqual(upgrade_decision.getSimulationState(), 'started')

  def testBase_acceptUpgradeDecision_started_decision(self):
    upgrade_decision = self._makeUpgradeDecision()
    upgrade_decision.setReference("UD-TESTSTARTED")
    upgrade_decision.start()
    self.tic()
    redirect_url = self.portal.Base_acceptUpgradeDecision('UD-TESTSTARTED')
    self.assertTrue(redirect_url.endswith(
     "?portal_status_message=This%20Upgrade%20Decision%20is%20already%20Started."), 
     "%s contains the wrong message" %  redirect_url)

  def testBase_acceptUpgradeDecision_stop_decision(self):
    upgrade_decision = self._makeUpgradeDecision()
    upgrade_decision.setReference("UD-TESTSTOP")
    upgrade_decision.start()
    upgrade_decision.stop()
    self.tic()
    redirect_url = self.portal.Base_acceptUpgradeDecision('UD-TESTSTOP')
    self.assertTrue(redirect_url.endswith(
      "?portal_status_message=This%20Upgrade%20Decision%20has%20been%20already%20processed."),
      "%s contains the wrong message" %  redirect_url)

  def testBase_acceptUpgradeDecision_delivered_decision(self):
    upgrade_decision = self._makeUpgradeDecision()
    upgrade_decision.setReference("UD-TESTDELIVERED")
    upgrade_decision.start()
    upgrade_decision.stop()
    upgrade_decision.deliver()
    self.tic()
    redirect_url = self.portal.Base_acceptUpgradeDecision('UD-TESTDELIVERED')
    self.assertTrue(redirect_url.endswith(
      "?portal_status_message=This%20Upgrade%20Decision%20has%20been%20already%20processed."),
      "%s contains the wrong message" %  redirect_url)

  def testBase_acceptUpgradeDecision_cancelled_decision(self):
    upgrade_decision = self._makeUpgradeDecision()
    upgrade_decision.setReference("UD-TESTCANCELLED")
    upgrade_decision.cancel()
    self.tic()
    redirect_url = self.portal.Base_acceptUpgradeDecision('UD-TESTCANCELLED')
    self.assertTrue(redirect_url.endswith(
      "?portal_status_message=Sorry%2C%20the%20upgrade%20is%20not%20possble%2C%20Upgrade%20Decision%20was%20Canceled%20or%20Rejected%21"),
      "%s contains the wrong message" %  redirect_url)

  def testBase_acceptUpgradeDecision_rejected_decision(self):
    upgrade_decision = self._makeUpgradeDecision()
    upgrade_decision.setReference("UD-TESTREJECT")
    upgrade_decision.cancel()
    self.tic()
    redirect_url = self.portal.Base_acceptUpgradeDecision('UD-TESTREJECT')
    self.assertTrue(redirect_url.endswith(
      "?portal_status_message=Sorry%2C%20the%20upgrade%20is%20not%20possble%2C%20Upgrade%20Decision%20was%20Canceled%20or%20Rejected%21"),
      "%s contains the wrong message" %  redirect_url)

  def testBase_rejectUpgradeDecision_no_reference(self):
    self._makeUpgradeDecision()
    self.assertRaises(ValueError, self.portal.Base_rejectUpgradeDecision, None)
    
  def testBase_rejectUpgradeDecision_duplicated_reference(self):
    upgrade_decision = self._makeUpgradeDecision()
    upgrade_decision.setReference("UD-TESTBADREFERENCE")
    upgrade_decision = self._makeUpgradeDecision()
    upgrade_decision.setReference("UD-TESTBADREFERENCE")
    self.tic()
    self.assertRaises(ValueError, self.portal.Base_acceptUpgradeDecision, None)

  def testBase_rejectUpgradeDecision_no_upgrade_decision(self):
    redirect_url = self.portal.Base_rejectUpgradeDecision('UD-UNEXISTING')
    self.assertTrue(redirect_url.endswith(
      "?portal_status_message=Unable%20to%20find%20the%20Upgrade%20Decision."), 
      "%s contains the wrong message" %  redirect_url)
     
  def testBase_rejectUpgradeDecision_draft_upgrade_decision(self):
    upgrade_decision = self._makeUpgradeDecision()
    upgrade_decision.setReference("UD-TESTDRAFT")
    self.tic()
    redirect_url = self.portal.Base_rejectUpgradeDecision('UD-TESTDRAFT')
    self.assertTrue(redirect_url.endswith(
      "?portal_status_message=Thanks%20Upgrade%20Decision%20has%20been"\
      "%20rejected%20Successfully%20%28You%20cannot%20use%20it%20anymore%29."), 
      "%s contains the wrong message" %  redirect_url)
    self.assertEqual(upgrade_decision.getSimulationState(), 'rejected')

  def testBase_rejectUpgradeDecision_planned_upgrade_decision(self):
    upgrade_decision = self._makeUpgradeDecision()
    upgrade_decision.setReference("UD-TESTPLANNED")
    upgrade_decision.plan()
    self.tic()
    redirect_url = self.portal.Base_rejectUpgradeDecision('UD-TESTPLANNED')
    self.assertTrue(redirect_url.endswith(
      "?portal_status_message=Thanks%20Upgrade%20Decision%20has%20been"\
      "%20rejected%20Successfully%20%28You%20cannot%20use%20it%20anymore%29."), 
      "%s contains the wrong message" %  redirect_url)
    self.assertEqual(upgrade_decision.getSimulationState(), 'rejected')

  def testBase_rejectUpgradeDecision_confirmed_upgrade_decision(self):
    upgrade_decision = self._makeUpgradeDecision()
    upgrade_decision.setReference("UD-TESTCONFIRMED")
    upgrade_decision.confirm()
    self.tic()
    redirect_url = self.portal.Base_rejectUpgradeDecision('UD-TESTCONFIRMED')
    self.assertTrue(redirect_url.endswith(
      "?portal_status_message=Thanks%20Upgrade%20Decision%20has%20been"\
      "%20rejected%20Successfully%20%28You%20cannot%20use%20it%20anymore%29."),
      "%s contains the wrong message" %  redirect_url)
    self.assertEqual(upgrade_decision.getSimulationState(), 'rejected')

  def testBase_rejectUpgradeDecision_started_decision(self):
    upgrade_decision = self._makeUpgradeDecision()
    upgrade_decision.setReference("UD-TESTSTARTED")
    upgrade_decision.start()
    self.tic()
    redirect_url = self.portal.Base_rejectUpgradeDecision('UD-TESTSTARTED')
    self.assertTrue(redirect_url.endswith(
     "?portal_status_message=Sorry%2C%20This%20Upgrade%20Decision%20is%20"\
     "already%20Started%2C%20you%20cannot%20reject%20it%20anymore."),
     "%s contains the wrong message" %  redirect_url)

  def testBase_rejectUpgradeDecision_stop_decision(self):
    upgrade_decision = self._makeUpgradeDecision()
    upgrade_decision.setReference("UD-TESTSTOP")
    upgrade_decision.start()
    upgrade_decision.stop()
    self.tic()
    redirect_url = self.portal.Base_rejectUpgradeDecision('UD-TESTSTOP')
    self.assertTrue(redirect_url.endswith(
      "?portal_status_message=Sorry%2C%20this%20Upgrade%20Decision%20has%20been%20already%20processed."),
      "%s contains the wrong message" %  redirect_url)

  def testBase_rejectUpgradeDecision_delivered_decision(self):
    upgrade_decision = self._makeUpgradeDecision()
    upgrade_decision.setReference("UD-TESTDELIVERED")
    upgrade_decision.start()
    upgrade_decision.stop()
    upgrade_decision.deliver()
    self.tic()
    redirect_url = self.portal.Base_rejectUpgradeDecision('UD-TESTDELIVERED')
    self.assertTrue(redirect_url.endswith(
      "?portal_status_message=Sorry%2C%20this%20Upgrade%20Decision%20has%20been%20already%20processed."),
      "%s contains the wrong message" %  redirect_url)

  def testBase_rejectUpgradeDecision_cancelled_decision(self):
    upgrade_decision = self._makeUpgradeDecision()
    upgrade_decision.setReference("UD-TESTCANCELLED")
    upgrade_decision.cancel()
    self.tic()
    redirect_url = self.portal.Base_rejectUpgradeDecision('UD-TESTCANCELLED')
    self.assertTrue(redirect_url.endswith(
      "?portal_status_message=Upgrade%20Decision%20is%20already%20Rejected%21"),
      "%s contains the wrong message" %  redirect_url)

  def testBase_rejectUpgradeDecision_reject_decision(self):
    upgrade_decision = self._makeUpgradeDecision()
    upgrade_decision.setReference("UD-TESTREJECT")
    upgrade_decision.reject()
    self.tic()
    redirect_url = self.portal.Base_rejectUpgradeDecision('UD-TESTREJECT')
    self.assertTrue(redirect_url.endswith(
      "?portal_status_message=Upgrade%20Decision%20is%20already%20Rejected%21"),
      "%s contains the wrong message" %  redirect_url)

  def testUpgradeDecision_isUpgradeFinished_compute_node(self):
    compute_node, _ = self._makeComputeNode()
    software_release = self._makeSoftwareRelease()
    upgrade_decision = self._makeUpgradeDecision()
    upgrade_decision_line = self._makeUpgradeDecisionLine(upgrade_decision)
    upgrade_decision_line.setAggregateValueList([software_release, compute_node])

    upgrade_decision.confirm()
    upgrade_decision.stop()
    
    self.assertFalse(upgrade_decision.UpgradeDecision_isUpgradeFinished())
    self._makeSoftwareInstallation( compute_node, 
                                   software_release.getUrlString())
    self.tic()
    self.assertTrue(upgrade_decision.UpgradeDecision_isUpgradeFinished())

  def testUpgradeDecision_requestChangeState_started(self):
    upgrade_decision = self._makeUpgradeDecision()
    upgrade_decision.setReference("UD-TESTDECISION")
    upgrade_decision.confirm()
    requested_state = "started"
    self.assertEqual(upgrade_decision.getSimulationState(), 'confirmed')
    upgrade_decision.UpgradeDecision_requestChangeState(requested_state)
    self.assertEqual(upgrade_decision.getSimulationState(), 'started')

  def testUpgradeDecision_requestChangeState_reject(self):
    upgrade_decision = self._makeUpgradeDecision()
    upgrade_decision.setReference("UD-TESTDECISION")
    upgrade_decision.confirm()
    requested_state = "rejected"
    self.assertEqual(upgrade_decision.getSimulationState(), 'confirmed')
    upgrade_decision.UpgradeDecision_requestChangeState(requested_state)
    self.assertEqual(upgrade_decision.getSimulationState(), 'rejected')

  def testUpgradeDecision_requestChangeState_stopped(self):
    upgrade_decision = self._makeUpgradeDecision()
    upgrade_decision.setReference("UD-TESTDECISION")
    upgrade_decision.confirm()
    upgrade_decision.stop()
    requested_state = "started"
    self.assertEqual(upgrade_decision.getSimulationState(), 'stopped')
    result = upgrade_decision.UpgradeDecision_requestChangeState(requested_state)
    self.assertEqual(upgrade_decision.getSimulationState(), 'stopped')
    self.assertEqual(result, "Transition from state %s to %s is not permitted" % (
                      upgrade_decision.getSimulationState(), requested_state))

  def testUpgradeDecision_requestChangeState_rejected(self):
    upgrade_decision = self._makeUpgradeDecision()
    upgrade_decision.setReference("UD-TESTDECISION")
    upgrade_decision.confirm()
    upgrade_decision.start()
    requested_state = "rejected"
    self.assertEqual(upgrade_decision.getSimulationState(), 'started')
    result = upgrade_decision.UpgradeDecision_requestChangeState(requested_state)
    self.assertEqual(upgrade_decision.getSimulationState(), 'started')
    self.assertEqual(result, "Transition from state %s to %s is not permitted" % (
                      upgrade_decision.getSimulationState(), requested_state))

  def testUpgradeDecision_isUpgradeFinished_instance_tree(self):
    instance_tree = self._makeInstanceTree()
    software_release = self._makeSoftwareRelease()
    upgrade_decision = self._makeUpgradeDecision()
    upgrade_decision_line = self._makeUpgradeDecisionLine(upgrade_decision)
    upgrade_decision_line.setAggregateValueList([software_release,
                                                instance_tree])

    upgrade_decision.confirm()
    upgrade_decision.stop()
    
    self.assertFalse(upgrade_decision.UpgradeDecision_isUpgradeFinished())
    instance_tree.setUrlString(software_release.getUrlString()) 
    self.assertTrue(upgrade_decision.UpgradeDecision_isUpgradeFinished())

  @simulate('NotificationTool_getDocumentValue',
            'reference=None',
  'assert reference == "slapos-upgrade-compute-node.notification"\n' \
  'return context.restrictedTraverse(' \
  'context.REQUEST["testUpgradeDecision_notify_compute_node"])')
  def testUpgradeDecision_notify_compute_node(self):
    person = self._makePerson()
    compute_node, _ = self._makeComputeNode()
    software_release = self._makeSoftwareRelease()
    software_product = self._makeSoftwareProduct()
    software_release.setAggregateValue(software_product)
    upgrade_decision = self._makeUpgradeDecision()
    upgrade_decision.edit(destination_decision_value=person)
    upgrade_decision_line = self._makeUpgradeDecisionLine(upgrade_decision)
    upgrade_decision_line.setAggregateValueList([software_release, compute_node])
    
    notification_message = self.portal.notification_message_module.newContent(
      portal_type="Notification Message",
      title='Test NM title %s' % self.new_id,
      text_content_substitution_mapping_method_id=
          "NotificationMessage_getSubstitutionMappingDictFromArgument",
      text_content="""${software_product_title}
${compute_node_title}
${compute_node_reference}
${software_release_name}
${software_release_reference}
${new_software_release_url}""",
      content_type='text/html',
      )
    self.portal.REQUEST\
        ['testUpgradeDecision_notify_compute_node'] = \
        notification_message.getRelativeUrl()
    
    self.tic()
    
    self.assertEqual(None, upgrade_decision.UpgradeDecision_notify())
    
    upgrade_decision.plan()
    
    self.tic()
    
    self.assertEqual(None, upgrade_decision.UpgradeDecision_notify())
    
    self.tic()
    
    self.assertEqual(upgrade_decision.getSimulationState(), 'confirmed')
    self.assertEqual(len(upgrade_decision.getFollowUpRelatedValueList()), 1)
    event = upgrade_decision.getFollowUpRelatedValue()
    
    self.assertEqual(event.getTitle(), 
     "New Software available for Installation at %s" % compute_node.getTitle())
     
    self.assertEqual(event.getTextContent().splitlines(),
      [software_product.getTitle(), compute_node.getTitle(), compute_node.getReference(),
       software_release.getTitle(), software_release.getReference(),
       software_release.getUrlString()])
      
      
    self.assertEqual(event.getSimulationState(), "delivered")

  @simulate('NotificationTool_getDocumentValue',
            'reference=None',
  'assert reference == "slapos-upgrade-instance-tree.notification"\n' \
  'return context.restrictedTraverse(' \
  'context.REQUEST["testUpgradeDecision_notify_instance_tree"])')
  def testUpgradeDecision_notify_instance_tree(self):
    person = self._makePerson()
    instance_tree = self._makeInstanceTree()
    software_release = self._makeSoftwareRelease()
    software_product = self._makeSoftwareProduct()
    software_release.setAggregateValue(software_product)
    upgrade_decision = self._makeUpgradeDecision()
    upgrade_decision.edit(destination_decision_value=person)
    upgrade_decision_line = self._makeUpgradeDecisionLine(upgrade_decision)
    upgrade_decision_line.setAggregateValueList([software_release, 
                                                instance_tree])

    old_url = instance_tree.getUrlString()

    notification_message = self.portal.notification_message_module.newContent(
      portal_type="Notification Message",
      title='Test NM title %s' % self.new_id,
      text_content_substitution_mapping_method_id=
          "NotificationMessage_getSubstitutionMappingDictFromArgument",
      text_content="""${software_product_title}
${instance_tree_title}
${old_software_release_url}
${software_release_name}
${software_release_reference}
${new_software_release_url}""",
      content_type='text/html',
      )
    self.portal.REQUEST\
        ['testUpgradeDecision_notify_instance_tree'] = \
        notification_message.getRelativeUrl()
    
    self.tic()
    
    self.assertEqual(None, upgrade_decision.UpgradeDecision_notify())
    
    upgrade_decision.plan()
    
    self.tic()
    
    self.assertEqual(None, upgrade_decision.UpgradeDecision_notify())
    
    self.tic()
    
    self.assertEqual(upgrade_decision.getSimulationState(), 'confirmed')
    self.assertEqual(len(upgrade_decision.getFollowUpRelatedValueList()), 1)
    event = upgrade_decision.getFollowUpRelatedValue()
    
    self.assertEqual(event.getTitle(), 
     "New Upgrade available for %s" % instance_tree.getTitle())
     
    self.assertEqual(event.getTextContent().splitlines(),
      [software_product.getTitle(), instance_tree.getTitle(), 
       old_url, software_release.getTitle(), software_release.getReference(),
       software_release.getUrlString()])

    self.assertEqual(event.getSimulationState(), "delivered")
    
    
  @simulate('NotificationTool_getDocumentValue',
            'reference=None',
  'assert reference == "slapos-upgrade-delivered-compute-node.notification"\n' \
  'return context.restrictedTraverse(' \
  'context.REQUEST["testUpgradeDecision_notifyDelivered_compute_node"])')
  @simulate('UpgradeDecision_isUpgradeFinished',
            '', 'return 1')
  def testUpgradeDecision_notifyDelivered_compute_node(self):
    person = self._makePerson()
    compute_node, _ = self._makeComputeNode()
    software_release = self._makeSoftwareRelease()
    software_product = self._makeSoftwareProduct()
    software_release.setAggregateValue(software_product)
    upgrade_decision = self._makeUpgradeDecision()
    upgrade_decision.edit(destination_decision_value=person)
    upgrade_decision_line = self._makeUpgradeDecisionLine(upgrade_decision)
    upgrade_decision_line.setAggregateValueList([software_release, compute_node])
    
    notification_message = self.portal.notification_message_module.newContent(
      portal_type="Notification Message",
      title='Test NM title %s' % self.new_id,
      text_content_substitution_mapping_method_id=
          "NotificationMessage_getSubstitutionMappingDictFromArgument",
      text_content="""${software_product_title}
${compute_node_title}
${compute_node_reference}
${software_release_name}
${software_release_reference}
${new_software_release_url}""",
      content_type='text/html',
      )
    self.portal.REQUEST\
        ['testUpgradeDecision_notifyDelivered_compute_node'] = \
        notification_message.getRelativeUrl()
    
    self.tic()
    
    self.assertEqual(None, upgrade_decision.UpgradeDecision_notifyDelivered())
    
    upgrade_decision.start()
    upgrade_decision.stop()
    
    self.tic()
    
    self.assertEqual(None, upgrade_decision.UpgradeDecision_notifyDelivered())
    
    self.tic()
    
    self.assertEqual(upgrade_decision.getSimulationState(), 'delivered')
    self.assertEqual(len(upgrade_decision.getFollowUpRelatedValueList()), 1)
    event = upgrade_decision.getFollowUpRelatedValue()
    
    self.assertEqual(event.getTitle(), 
      "Upgrade processed at %s for %s" % (compute_node.getTitle(), 
                                          software_release.getReference()))
     
    self.assertEqual(event.getTextContent().splitlines(),
      [software_product.getTitle(), compute_node.getTitle(), compute_node.getReference(),
       software_release.getTitle(), software_release.getReference(),
       software_release.getUrlString()])
      
    self.assertEqual(event.getSimulationState(), "delivered")

  @simulate('NotificationTool_getDocumentValue',
            'reference=None',
  'assert reference == "slapos-upgrade-delivered-instance-tree.notification"\n' \
  'return context.restrictedTraverse(' \
  'context.REQUEST["testUpgradeDecision_notifyDelivered_instance_tree"])')
  @simulate('UpgradeDecision_isUpgradeFinished',
            '', 'return 1')
  def testUpgradeDecision_notifyDelivered_instance_tree(self):
    person = self._makePerson()
    instance_tree = self._makeInstanceTree()
    software_release = self._makeSoftwareRelease()
    software_product = self._makeSoftwareProduct()
    software_release.setAggregateValue(software_product)
    upgrade_decision = self._makeUpgradeDecision()
    upgrade_decision.edit(destination_decision_value=person)
    upgrade_decision_line = self._makeUpgradeDecisionLine(upgrade_decision)
    upgrade_decision_line.setAggregateValueList([software_release, 
                                                instance_tree])

    old_url = instance_tree.getUrlString()

    notification_message = self.portal.notification_message_module.newContent(
      portal_type="Notification Message",
      title='Test NM title %s' % self.new_id,
      text_content_substitution_mapping_method_id=
          "NotificationMessage_getSubstitutionMappingDictFromArgument",
      text_content="""${software_product_title}
${instance_tree_title}
${old_software_release_url}
${software_release_name}
${software_release_reference}
${new_software_release_url}""",
      content_type='text/html',
      )
    self.portal.REQUEST\
        ['testUpgradeDecision_notifyDelivered_instance_tree'] = \
        notification_message.getRelativeUrl()
    
    self.tic()
    
    self.assertEqual(None, upgrade_decision.UpgradeDecision_notifyDelivered())
    
    upgrade_decision.start()
    upgrade_decision.stop()
    
    self.tic()
    
    self.assertEqual(None, upgrade_decision.UpgradeDecision_notifyDelivered())
    
    self.tic()
    
    self.assertEqual(upgrade_decision.getSimulationState(), 'delivered')
    self.assertEqual(len(upgrade_decision.getFollowUpRelatedValueList()), 1)
    event = upgrade_decision.getFollowUpRelatedValue()
    
    self.assertEqual(event.getTitle(),
      "Upgrade Processed for %s (%s)" % (instance_tree.getTitle(), 
                                              software_release.getReference()))
     
    self.assertEqual(event.getTextContent().splitlines(),
      [software_product.getTitle(), instance_tree.getTitle(), 
       old_url, software_release.getTitle(), software_release.getReference(),
       software_release.getUrlString()])

    self.assertEqual(event.getSimulationState(), "delivered")

  def testUpgradeDecisionLine_cancel_already_cancelled(self):
    software_release = self._makeSoftwareRelease()
    upgrade_decision = self._makeUpgradeDecision()
    upgrade_decision.cancel(comment="Cancelled by the test")
    upgrade_decision_line = self._makeUpgradeDecisionLine(upgrade_decision)
    upgrade_decision_line.setAggregateValueList([software_release])
    self.tic()

    upgrade_decision_line.UpgradeDecisionLine_cancel()
    self.assertEqual('cancelled', upgrade_decision.getSimulationState())
    workflow_history_list = upgrade_decision.Base_getWorkflowHistoryItemList('upgrade_decision_workflow', display=0)
    self.assertEqual("Cancelled by the test", workflow_history_list[-1].comment)

  def testUpgradeDecisionLine_cancel_archived_software_release(self):
    software_release = self._makeSoftwareRelease()
    upgrade_decision = self._makeUpgradeDecision()
    upgrade_decision_line = self._makeUpgradeDecisionLine(upgrade_decision)
    upgrade_decision_line.setAggregateValueList([software_release])
    self.tic()

    software_release.archive()
    upgrade_decision_line.UpgradeDecisionLine_cancel()
    self.assertEqual('cancelled', upgrade_decision.getSimulationState())
    workflow_history_list = upgrade_decision.Base_getWorkflowHistoryItemList('upgrade_decision_workflow', display=0)
    self.assertEqual("Software Release is archived.", workflow_history_list[-1].comment)

  @simulate('NotificationTool_getDocumentValue',
            'reference=None',
  'assert reference == "slapos-upgrade-delivered-compute-node.notification"\n' \
  'return context.restrictedTraverse(' \
  'context.REQUEST["testUpgradeDecisionLine_cancel_destroyed_instance_tree"])')
  def testUpgradeDecisionLine_cancel_destroyed_instance_tree(self):
    software_release = self._makeSoftwareRelease()
    instance_tree = self._makeFullInstanceTree(software_release.getUrlString())
    upgrade_decision = self._makeUpgradeDecision()

    upgrade_decision_line = self._makeUpgradeDecisionLine(upgrade_decision)
    upgrade_decision_line.setAggregateValueList([software_release, instance_tree])

    notification_message = self.portal.notification_message_module.newContent(
      portal_type="Notification Message",
      title='Test NM title %s' % self.new_id,
      text_content_substitution_mapping_method_id=
          "NotificationMessage_getSubstitutionMappingDictFromArgument",
      text_content="""${software_product_title}
${compute_node_title}
${compute_node_reference}
${software_release_name}
${software_release_reference}
${new_software_release_url}""",
      content_type='text/html',
      )
    self.portal.REQUEST\
        ['testUpgradeDecisionLine_cancel_destroyed_instance_tree'] = \
        notification_message.getRelativeUrl()
    self.tic()

    kw = dict(
      software_release = instance_tree.getUrlString(),
      software_type = instance_tree.getSourceReference(),
      instance_xml = instance_tree.getTextContent(),
      sla_xml = self.generateSafeXml(),
      shared = False
    )
    instance_tree.requestDestroy(**kw)
    self.tic()
    upgrade_decision_line.UpgradeDecisionLine_cancel()
    self.assertEqual('cancelled', upgrade_decision.getSimulationState())
    workflow_history_list = upgrade_decision.Base_getWorkflowHistoryItemList('upgrade_decision_workflow', display=0)
    self.assertEqual("Instance Tree is destroyed.", workflow_history_list[-1].comment)

  @simulate('NotificationTool_getDocumentValue',
            'reference=None',
  'assert reference == "slapos-upgrade-delivered-compute-node.notification"\n' \
  'return context.restrictedTraverse(' \
  'context.REQUEST["testUpgradeDecisionLine_cancel_destroyed_instance_tree"])')
  def testUpgradeDecisionLine_cancel_destroyed_instance_tree_and_disabled_monitor(self):
    software_release = self._makeSoftwareRelease()
    instance_tree = self._makeFullInstanceTree(software_release.getUrlString())
    upgrade_decision = self._makeUpgradeDecision()

    upgrade_decision_line = self._makeUpgradeDecisionLine(upgrade_decision)
    upgrade_decision_line.setAggregateValueList([software_release, instance_tree])

    notification_message = self.portal.notification_message_module.newContent(
      portal_type="Notification Message",
      title='Test NM title %s' % self.new_id,
      text_content_substitution_mapping_method_id=
          "NotificationMessage_getSubstitutionMappingDictFromArgument",
      text_content="""${software_product_title}
${compute_node_title}
${compute_node_reference}
${software_release_name}
${software_release_reference}
${new_software_release_url}""",
      content_type='text/html',
      )
    self.portal.REQUEST\
        ['testUpgradeDecisionLine_cancel_destroyed_instance_tree'] = \
        notification_message.getRelativeUrl()
    self.tic()

    kw = dict(
      software_release = instance_tree.getUrlString(),
      software_type = instance_tree.getSourceReference(),
      instance_xml = instance_tree.getTextContent(),
      sla_xml = self.generateSafeXml(),
      shared = False
    )
    instance_tree.requestDestroy(**kw)
    instance_tree.setMonitorScope("disabled")
    self.tic()
    upgrade_decision_line.UpgradeDecisionLine_cancel()
    self.assertEqual('cancelled', upgrade_decision.getSimulationState())
    workflow_history_list = upgrade_decision.Base_getWorkflowHistoryItemList('upgrade_decision_workflow', display=0)
    self.assertEqual("Instance Tree is destroyed.", workflow_history_list[-1].comment)

  @simulate('NotificationTool_getDocumentValue',
            'reference=None',
  'assert reference == "slapos-upgrade-delivered-compute-node.notification"\n' \
  'return context.restrictedTraverse(' \
  'context.REQUEST["testUpgradeDecisionLine_cancel_destroyed_hs_archived_sr"])')
  def testUpgradeDecisionLine_cancel_destroyed_hs_archived_sr(self):
    software_release = self._makeSoftwareRelease()
    instance_tree = self._makeFullInstanceTree(software_release.getUrlString())
    upgrade_decision = self._makeUpgradeDecision()

    upgrade_decision_line = self._makeUpgradeDecisionLine(upgrade_decision)
    upgrade_decision_line.setAggregateValueList([software_release, instance_tree])

    notification_message = self.portal.notification_message_module.newContent(
      portal_type="Notification Message",
      title='Test NM title %s' % self.new_id,
      text_content_substitution_mapping_method_id=
          "NotificationMessage_getSubstitutionMappingDictFromArgument",
      text_content="""${software_product_title}
${compute_node_title}
${compute_node_reference}
${software_release_name}
${software_release_reference}
${new_software_release_url}""",
      content_type='text/html',
      )
    self.portal.REQUEST\
        ['testUpgradeDecisionLine_cancel_destroyed_hs_archived_sr'] = \
        notification_message.getRelativeUrl()
    self.tic()

    kw = dict(
      software_release = instance_tree.getUrlString(),
      software_type = instance_tree.getSourceReference(),
      instance_xml = instance_tree.getTextContent(),
      sla_xml = self.generateSafeXml(),
      shared = False
    )
    instance_tree.requestDestroy(**kw)
    software_release.archive()
    self.tic()
    upgrade_decision_line.UpgradeDecisionLine_cancel()
    self.assertEqual('cancelled', upgrade_decision.getSimulationState())
    workflow_history_list = upgrade_decision.Base_getWorkflowHistoryItemList('upgrade_decision_workflow', display=0)
    self.assertEqual("Software Release is archived.", workflow_history_list[-1].comment)

