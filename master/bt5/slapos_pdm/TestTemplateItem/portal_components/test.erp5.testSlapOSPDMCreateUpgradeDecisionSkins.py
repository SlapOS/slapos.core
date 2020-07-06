# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2019 Nexedi SA and Contributors. All Rights Reserved.
#
# This program is free software: you can Use, Study, Modify and Redistribute
# it under the terms of the GNU General Public License version 3, or (at your
# option) any later version, as published by the Free Software Foundation.
#
# You can also Link and Combine this program with other software covered by
# the terms of any of the Free Software licenses or any of the Open Source
# Initiative approved licenses and Convey the resulting work. Corresponding
# source of such a combination shall include the source code for all other
# software used.
#
# This program is distributed WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See COPYING file for full licensing terms.
# See https://www.nexedi.com/licensing for rationale and options.
#
##############################################################################

from erp5.component.test.testSlapOSPDMSkins import TestSlapOSPDMMixinSkins
from DateTime import DateTime
import transaction

class TestSlapOSPDMCreateUpgradeDecisionSkins(TestSlapOSPDMMixinSkins):
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

  def _installSoftwareOnTheComputer(self, software_release_url_list):
    for software_release in software_release_url_list:
      software_installation = self.portal.software_installation_module\
        .newContent(portal_type='Software Installation',
        url_string=software_release,
        aggregate=self.computer.getRelativeUrl())
      software_installation.validate()
      software_installation.requestStart()
    self.tic()

  def _createInstance(self, url_string, shared=False):
    hosting_subscription = self.portal.hosting_subscription_module\
        .template_hosting_subscription.Base_createCloneDocument(batch_mode=1)
    hosting_subscription.edit(
    )
    hosting_subscription.validate()
    hosting_subscription.edit(
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
      software_title=hosting_subscription.getTitle(),
      state='started'
    )
    hosting_subscription.requestStart(**request_kw)
    hosting_subscription.requestInstance(**request_kw)

    instance = hosting_subscription.getPredecessorValue()
    self.tic()
    return hosting_subscription, instance

  def _makeTree(self, software_release_url):
    self.hosting_subscription, self.instance = self._createInstance(software_release_url)
    self.shared_hosting_subscription, self.shared_instance = self._createInstance(software_release_url, True)
    self.instance.setAggregate(self.partition.getRelativeUrl())
    self.shared_instance.setAggregate(self.partition.getRelativeUrl())
    self.partition.markBusy()
    self.tic()

  def afterSetUp(self):
    TestSlapOSPDMMixinSkins.afterSetUp(self)
    preference =  self.portal.portal_preferences.getActiveSystemPreference()
    preference.setPreferredCloudContractEnabled(True)
    self.tic()
    self._makeComputer()
    self._makeSoftwareProductCatalog()
    self._installSoftwareOnTheComputer([
      self.previous_software_release.getUrlString(),
      self.new_software_release.getUrlString()
    ])
    self.person = self.makePerson()
    self.tic()
    self._makeTree(self.previous_software_release.getUrlString())

  def test_HostingSubscription_createUpgradeDecision_upgradeScopeConfirmation(self):
    # check upgrade decision on HS
    self.hosting_subscription.setUpgradeScope('manual')
    self.tic()
    upgrade_decision = self.hosting_subscription.HostingSubscription_createUpgradeDecision()
    self.assertEqual('planned', upgrade_decision.getSimulationState())
    shared_upgrade_decision = self.shared_hosting_subscription.HostingSubscription_createUpgradeDecision()
    self.assertEqual(None, shared_upgrade_decision)

    # simulate upgrade of the hosting subscription
    upgrade_decision.confirm()
    upgrade_decision.start()
    upgrade_decision.stop()
    upgrade_decision.deliver()
    self.hosting_subscription.edit(url_string=self.new_software_release.getUrlString())
    self.instance.edit(url_string=self.new_software_release.getUrlString())
    self.tic()

    # check upgrade decision on shared HS related to upgraded HS
    self.shared_hosting_subscription.setUpgradeScope('manual')

    shared_upgrade_decision = self.shared_hosting_subscription.HostingSubscription_createUpgradeDecision()
    self.assertEqual('started', shared_upgrade_decision.getSimulationState())

  def test_HostingSubscription_createUpgradeDecision_upgradeScopeAuto(self):
    # check upgrade decision on HS
    self.hosting_subscription.setUpgradeScope('auto')
    self.tic()
    upgrade_decision = self.hosting_subscription.HostingSubscription_createUpgradeDecision()
    self.assertEqual('started', upgrade_decision.getSimulationState())
    shared_upgrade_decision = self.shared_hosting_subscription.HostingSubscription_createUpgradeDecision()
    self.assertEqual(None, shared_upgrade_decision)

    # simulate upgrade of the hosting subscription
    upgrade_decision.stop()
    upgrade_decision.deliver()
    self.hosting_subscription.edit(url_string=self.new_software_release.getUrlString())
    self.instance.edit(url_string=self.new_software_release.getUrlString())
    self.tic()

    # check upgrade decision on shared HS related to upgraded HS
    self.shared_hosting_subscription.setUpgradeScope('auto')

    shared_upgrade_decision = self.shared_hosting_subscription.HostingSubscription_createUpgradeDecision()
    self.assertEqual('started', shared_upgrade_decision.getSimulationState())

  def test_HostingSubscription_createUpgradeDecision_upgradeScopeDisabled(self):
    # check upgrade decision on HS
    self.hosting_subscription.setUpgradeScope('disabled')
    self.tic()
    upgrade_decision = self.hosting_subscription.HostingSubscription_createUpgradeDecision()
    self.assertEqual(None, upgrade_decision)
    shared_upgrade_decision = self.shared_hosting_subscription.HostingSubscription_createUpgradeDecision()
    self.assertEqual(None, shared_upgrade_decision)


  def testHostingSubscription_createUpgradeDecision_no_newer(self):
    person = self._makePerson()
    computer, _ = self._makeComputer(owner=person)
    self._makeComputerPartitions(computer)
    software_product = self._makeSoftwareProduct()
    software_release = self._requestSoftwareRelease(
                                    software_product.getRelativeUrl())
    url_string = software_release.getUrlString()
    self._makeSoftwareInstallation(computer, url_string)
    self.tic()

    # Create Hosting Subscription
    hosting_subscription = self._makeFullHostingSubscription(
                                    url_string, person)
    self.tic()
    
    upgrade_decision = hosting_subscription.HostingSubscription_createUpgradeDecision()
    self.assertEqual(upgrade_decision, None)
    
    self._makeFullSoftwareInstance(hosting_subscription, url_string)
    self._markComputerPartitionBusy(computer,
                                    hosting_subscription.getPredecessorValue())
    
    self._requestSoftwareRelease(software_product.getRelativeUrl())
    self.tic()
    
    upgrade_decision = hosting_subscription.HostingSubscription_createUpgradeDecision()
    self.assertEqual(upgrade_decision, None)

  def testHostingSubscription_createUpgradeDecision_closed_computer(self):
    person = self._makePerson()
    computer, _ = self._makeComputer(owner=person, allocation_scope="close/outdated")
    self._makeComputerPartitions(computer)
    software_product = self._makeSoftwareProduct()
    software_release = self._requestSoftwareRelease(
                                    software_product.getRelativeUrl())
    url_string = software_release.getUrlString()
    
    self._makeSoftwareInstallation( computer, url_string)
    
    # Create Hosting Subscription and Software Instance
    hosting_subscription = self._makeFullHostingSubscription(
                                    url_string, person)
    self._makeFullSoftwareInstance(hosting_subscription, url_string)
    self._markComputerPartitionBusy(computer,
                                    hosting_subscription.getPredecessorValue())
    
    # Install the Newest software release
    software_release2 = self._requestSoftwareRelease(
                                      software_product.getRelativeUrl())
    self._makeSoftwareInstallation(computer,
                                    software_release2.getUrlString())
    self.tic()
    
    up_decision = hosting_subscription.HostingSubscription_createUpgradeDecision()
    self.assertEqual(up_decision, None)

  def testHostingSubscription_createUpgradeDecision_create_once_transaction(self):
    person = self._makePerson()
    computer, _ = self._makeComputer(owner=person, allocation_scope="open/personal")
    self._makeComputerPartitions(computer)
    software_product = self._makeSoftwareProduct()
    software_release = self._requestSoftwareRelease(
                                    software_product.getRelativeUrl())
    url_string = software_release.getUrlString()
    
    self._makeSoftwareInstallation( computer, url_string)
    
    # Create Hosting Subscription and Software Instance
    hosting_subscription = self._makeFullHostingSubscription(
                                    url_string, person)
    self._makeFullSoftwareInstance(hosting_subscription, url_string)
    self._markComputerPartitionBusy(computer,
                                    hosting_subscription.getPredecessorValue())
    
    # Install the Newest software release
    software_release2 = self._requestSoftwareRelease(
                                      software_product.getRelativeUrl())
    self._makeSoftwareInstallation(computer,
                                    software_release2.getUrlString())
    self.tic()
    
    up_decision = hosting_subscription.HostingSubscription_createUpgradeDecision()
    self.assertNotEqual(up_decision, None)
    self.assertEqual(up_decision.getSimulationState(), 'planned')
    transaction.commit()
    # call a second time without tic
    up_decision = hosting_subscription.HostingSubscription_createUpgradeDecision()
    # no new Upgrade decision created
    self.assertEqual(up_decision, None)

  def testHostingSubscription_createUpgradeDecision(self):
    person = self._makePerson()
    computer, _ = self._makeComputer(owner=person)
    self._makeComputerPartitions(computer)
    software_product = self._makeSoftwareProduct()
    software_release = self._requestSoftwareRelease(
                                    software_product.getRelativeUrl())
    url_string = software_release.getUrlString()
    
    self._makeSoftwareInstallation( computer, url_string)
    
    # Create Hosting Subscription and Software Instance
    hosting_subscription = self._makeFullHostingSubscription(
                                    url_string, person)
    self._makeFullSoftwareInstance(hosting_subscription, url_string)
    self._markComputerPartitionBusy(computer,
                                    hosting_subscription.getPredecessorValue())
    
    # Install the Newest software release
    software_release2 = self._requestSoftwareRelease(
                                      software_product.getRelativeUrl())
    self._makeSoftwareInstallation(computer,
                                    software_release2.getUrlString())
    self.tic()
    
    up_decision = hosting_subscription.HostingSubscription_createUpgradeDecision()
    self.assertNotEqual(up_decision, None)
    self.assertEqual(up_decision.getSimulationState(), 'planned')
    
    self.assertEqual(up_decision.UpgradeDecision_getHostingSubscription().\
                      getReference(), hosting_subscription.getReference())

    self.assertEqual(up_decision.UpgradeDecision_getSoftwareRelease().\
                              getUrlString(), software_release2.getUrlString())
    
    self.tic()
    up_decision2 = hosting_subscription.HostingSubscription_createUpgradeDecision()
    self.assertEqual(up_decision2, None)
  
  
  def testHostingSubscription_createUpgradeDecision_with_exist(self):
    person = self._makePerson()
    computer, _ = self._makeComputer(owner=person)
    self._makeComputerPartitions(computer)
    software_product = self._makeSoftwareProduct()
    software_release = self._requestSoftwareRelease(
                                    software_product.getRelativeUrl())
    url_string = software_release.getUrlString()
    
    self._makeSoftwareInstallation( computer, url_string)
    
    # Create Hosting Subscription and Software Instance
    hosting_subscription = self._makeFullHostingSubscription(
                                    url_string, person)
    self._makeFullSoftwareInstance(hosting_subscription, url_string)
    self._markComputerPartitionBusy(computer,
                                    hosting_subscription.getPredecessorValue())
    
    # Install the Newest software release
    software_release2 = self._requestSoftwareRelease(
                                      software_product.getRelativeUrl())
    self._makeSoftwareInstallation(computer, software_release2.getUrlString())
    self.tic()
    
    up_decision = hosting_subscription.HostingSubscription_createUpgradeDecision()
    self.assertEqual(up_decision.getSimulationState(), 'planned')
    
    # Install the another software release
    software_release3 = self._requestSoftwareRelease(
      software_product.getRelativeUrl())
    self._makeSoftwareInstallation(computer, software_release3.getUrlString())
    self.tic()
    
    up_decision2 = hosting_subscription.HostingSubscription_createUpgradeDecision()
    self.assertEqual(up_decision2.getSimulationState(), 'planned')
    self.assertEqual(up_decision.getSimulationState(), 'cancelled')
    release = up_decision2.UpgradeDecision_getSoftwareRelease()
    self.assertEqual(release.getUrlString(),
                                software_release3.getUrlString())

  def testHostingSubscription_createUpgradeDecision_rejected(self):
    person = self._makePerson()
    computer, _ = self._makeComputer(owner=person)
    self._makeComputerPartitions(computer)
    software_product = self._makeSoftwareProduct()
    software_release = self._requestSoftwareRelease(
                                    software_product.getRelativeUrl())
    url_string = software_release.getUrlString()
    
    self._makeSoftwareInstallation(computer, url_string)
    
    # Create Hosting Subscription and Software Instance
    hosting_subscription = self._makeFullHostingSubscription(
                                    url_string, person)
    self._makeFullSoftwareInstance(hosting_subscription, url_string)
    self._markComputerPartitionBusy(computer,
                                    hosting_subscription.getPredecessorValue())
    
    # Install the Newest software release
    software_release2 = self._requestSoftwareRelease(
                                      software_product.getRelativeUrl())
    self._makeSoftwareInstallation(computer, software_release2.getUrlString())
    self.tic()
    
    up_decision = hosting_subscription.HostingSubscription_createUpgradeDecision()
    self.assertEqual(up_decision.getSimulationState(), 'planned')
    
    # Reject upgrade decision
    up_decision.reject()
    self.tic()
    
    in_progress = software_release2.SoftwareRelease_getUpgradeDecisionInProgress(
                                hosting_subscription.getUid())
    up_decision = hosting_subscription.HostingSubscription_createUpgradeDecision()
    # There is an upgrade decision in progress
    self.assertNotEqual(in_progress, None)
    # No new upgrade decision created with software_release2
    self.assertEqual(up_decision, None)

  def testHostingSubscription_createUpgradeDecision_rejected_2(self):
    person = self._makePerson()
    computer, _ = self._makeComputer(owner=person)
    self._makeComputerPartitions(computer)
    software_product = self._makeSoftwareProduct()
    software_release = self._requestSoftwareRelease(
                                    software_product.getRelativeUrl())
    url_string = software_release.getUrlString()
    
    self._makeSoftwareInstallation(computer, url_string)
    
    # Create Hosting Subscription and Software Instance
    hosting_subscription = self._makeFullHostingSubscription(
                                    url_string, person)
    self._makeFullSoftwareInstance(hosting_subscription, url_string)
    self._markComputerPartitionBusy(computer,
                                    hosting_subscription.getPredecessorValue())
    
    # Install the Newest software release
    software_release2 = self._requestSoftwareRelease(
                                      software_product.getRelativeUrl())
    self._makeSoftwareInstallation(computer, software_release2.getUrlString())
    self.tic()
    
    up_decision = hosting_subscription.HostingSubscription_createUpgradeDecision()
    self.assertEqual(up_decision.getSimulationState(), 'planned')
    
    # Reject upgrade decision
    up_decision.reject()
    self.tic()
    
    # Install the another software release
    software_release3 = self._requestSoftwareRelease(
                                      software_product.getRelativeUrl())
    self._makeSoftwareInstallation(computer, software_release3.getUrlString())
    self.tic()
    
    decision2 = hosting_subscription.HostingSubscription_createUpgradeDecision()
    self.assertEqual(decision2.getSimulationState(), 'planned')
    self.assertEqual(up_decision.getSimulationState(), 'rejected')
    release = decision2.UpgradeDecision_getSoftwareRelease()
    self.assertEqual(release.getUrlString(),
                                software_release3.getUrlString())
  