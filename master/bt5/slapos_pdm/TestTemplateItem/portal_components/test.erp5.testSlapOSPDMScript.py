# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2019 Nexedi SA and Contributors. All Rights Reserved.
#
##############################################################################

from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixin
from DateTime import DateTime
class TestSlapOSPDMScript(SlapOSTestCaseMixin):
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
    SlapOSTestCaseMixin.afterSetUp(self)
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