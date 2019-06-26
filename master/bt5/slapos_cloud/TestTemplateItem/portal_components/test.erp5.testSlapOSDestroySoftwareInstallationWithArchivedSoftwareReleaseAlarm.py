# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2019 Nexedi SA and Contributors. All Rights Reserved.
#
##############################################################################

from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixin

class TestSlapOSDestroySoftwareInstallationWithArchivedSoftwareReleaseAlarm(SlapOSTestCaseMixin):
  def createInstance(self, url_string):
    hosting_subscription = self.portal.hosting_subscription_module\
        .template_hosting_subscription.Base_createCloneDocument(batch_mode=1)
    hosting_subscription.edit(
    )
    hosting_subscription.validate()
    hosting_subscription.edit(
        title=self.generateNewSoftwareTitle(),
        reference="TESTHS-%s" % self.generateNewId(),
    )
    request_kw = dict(
      software_release=url_string,
      software_type=self.generateNewSoftwareType(),
      instance_xml=self.generateSafeXml(),
      sla_xml=self.generateSafeXml(),
      shared=False,
      software_title=hosting_subscription.getTitle(),
      state='started'
    )
    hosting_subscription.requestStart(**request_kw)
    hosting_subscription.requestInstance(**request_kw)

    instance = hosting_subscription.getPredecessorValue()
    self.tic()
    return instance

  def test(self):
    preference =  self.portal.portal_preferences.getActiveSystemPreference()
    preference.setPreferredCloudContractEnabled(True)
    self.tic()
    computer, partition = self._makeComputer()
    archived_url_string = self.generateNewSoftwareReleaseUrl()
    # create software release
    archived_software_release = self.portal.software_release_module.newContent(
      portal_type='Software Release',
      version='1',
      url_string=archived_url_string
    )
    archived_software_release.publish()
    archived_software_release.archive()
    self.assertEqual('draft', archived_software_release.getSimulationState())
    # install an software release
    archived_software_installation = self.portal.software_installation_module\
        .newContent(portal_type='Software Installation',
        url_string=archived_url_string,
        aggregate=computer.getRelativeUrl())
    archived_software_installation.validate()
    archived_software_installation.requestStart()

    archived_used_url_string = self.generateNewSoftwareReleaseUrl()
    # create software release
    archived_used_software_release = self.portal.software_release_module.newContent(
      portal_type='Software Release',
      version='1',
      url_string=archived_used_url_string
    )
    archived_used_software_release.publish()
    archived_used_software_release.archive()
    self.assertEqual('draft', archived_used_software_release.getSimulationState())
    # install an software release
    archived_used_software_installation = self.portal.software_installation_module\
        .newContent(portal_type='Software Installation',
        url_string=archived_used_url_string,
        aggregate=computer.getRelativeUrl())
    archived_used_software_installation.validate()
    archived_used_software_installation.requestStart()

    # use the software release
    instance = self.createInstance(archived_used_url_string)
    instance.setAggregate(partition.getRelativeUrl())
    partition.markBusy()
    self.tic()

    published_url_string = self.generateNewSoftwareReleaseUrl()
    # create software release
    published_software_release = self.portal.software_release_module.newContent(
      portal_type='Software Release',
      version='1',
      url_string=published_url_string
    )
    published_software_release.publish()
    self.assertEqual('draft', published_software_release.getSimulationState())
    # install an software release
    published_software_installation = self.portal.software_installation_module\
        .newContent(portal_type='Software Installation',
        url_string=published_url_string,
        aggregate=computer.getRelativeUrl())
    published_software_installation.validate()
    published_software_installation.requestStart()


    self.tic()

    # first run touches software installation
    self.stepCallSlaposDestroySoftwareInstallationWithArchivedSoftwareReleaseAlarm()
    self.tic()
    self.assertEqual('destroy_requested', archived_software_installation.getSlapState())
    self.assertEqual('validated', archived_software_installation.getValidationState())

    self.assertEqual('start_requested', published_software_installation.getSlapState())
    self.assertEqual('validated', published_software_installation.getValidationState())

    self.assertEqual('start_requested', archived_used_software_installation.getSlapState())
    self.assertEqual('validated', archived_used_software_installation.getValidationState())

    # second run, but it is still not reported that software installation is destroyed
    self.stepCallSlaposDestroySoftwareInstallationWithArchivedSoftwareReleaseAlarm()
    self.tic()
    self.assertEqual('draft', archived_software_release.getSimulationState())
    self.assertEqual('draft', published_software_release.getSimulationState())
    self.assertEqual('start_requested', published_software_installation.getSlapState())
    self.assertEqual('validated', archived_used_software_installation.getValidationState())
    self.assertEqual('start_requested', archived_used_software_installation.getSlapState())

    # simulate the computer run
    archived_software_installation.invalidate()
    self.tic()
    self.stepCallSlaposDestroySoftwareInstallationWithArchivedSoftwareReleaseAlarm()
    self.tic()
    self.assertEqual('cleaned', archived_software_release.getSimulationState())
    self.assertEqual('draft', published_software_release.getSimulationState())
    self.assertEqual('start_requested', published_software_installation.getSlapState())
    self.assertEqual('validated', archived_used_software_installation.getValidationState())
    self.assertEqual('start_requested', archived_used_software_installation.getSlapState())

  def test_no_op_run(self):
    self.fail('Prove that alarm does not spawn activities in case if all SRs are cleaned')
