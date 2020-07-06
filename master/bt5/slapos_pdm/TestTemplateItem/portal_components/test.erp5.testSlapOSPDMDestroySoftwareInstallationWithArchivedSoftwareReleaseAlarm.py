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

from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixin
from erp5.component.test.testSlapOSAccountingAlarm import simulateByEditWorkflowMark

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
    self.stepCallSlaposPdmDestroySoftwareInstallationWithArchivedSoftwareReleaseAlarm()
    self.tic()
    self.assertEqual('destroy_requested', archived_software_installation.getSlapState())
    self.assertEqual('validated', archived_software_installation.getValidationState())

    self.assertEqual('start_requested', published_software_installation.getSlapState())
    self.assertEqual('validated', published_software_installation.getValidationState())

    self.assertEqual('start_requested', archived_used_software_installation.getSlapState())
    self.assertEqual('validated', archived_used_software_installation.getValidationState())

    self.assertEqual('draft', archived_software_release.getSimulationState())
    self.assertEqual('draft', published_software_release.getSimulationState())
    
    # second run, but it is still not reported that software installation is destroyed
    self.stepCallSlaposPdmDestroySoftwareInstallationWithArchivedSoftwareReleaseAlarm()
    self.tic()
    
    self.assertEqual('cleaned', archived_software_release.getSimulationState())
    self.assertEqual('draft', published_software_release.getSimulationState())
    self.assertEqual('start_requested', published_software_installation.getSlapState())
    self.assertEqual('validated', archived_used_software_installation.getValidationState())
    self.assertEqual('start_requested', archived_used_software_installation.getSlapState())

  @simulateByEditWorkflowMark('SoftwareRelease_findAndDestroySoftwareInstallation')
  def test_no_op_run_software_release(self):
    archived_software_release = self.portal.software_release_module.newContent(
      portal_type='Software Release',
      version='1',
      url_string=self.generateNewSoftwareReleaseUrl(),
    )
    archived_software_release.publish()
    archived_software_release.archive()
    self.assertEqual('draft', archived_software_release.getSimulationState())

    archived_cleaned_software_release = self.portal.software_release_module.newContent(
      portal_type='Software Release',
      version='1',
      url_string=self.generateNewSoftwareReleaseUrl(),
    )
    archived_cleaned_software_release.publish()
    archived_cleaned_software_release.archive()
    archived_cleaned_software_release.cleanup()
    self.assertEqual('cleaned', archived_cleaned_software_release.getSimulationState())

    published_software_release = self.portal.software_release_module.newContent(
      portal_type='Software Release',
      version='1',
      url_string=self.generateNewSoftwareReleaseUrl(),
    )
    published_software_release.publish()
    self.assertEqual('draft', published_software_release.getSimulationState())
    self.tic()

    self.stepCallSlaposPdmDestroySoftwareInstallationWithArchivedSoftwareReleaseAlarm()
    self.tic()

    v = 'Visited by SoftwareRelease_findAndDestroySoftwareInstallation'
    self.assertFalse(v in
      [q['comment'] for q in published_software_release.workflow_history['edit_workflow']])
    self.assertFalse(v in
      [q['comment'] for q in archived_cleaned_software_release.workflow_history['edit_workflow']])
    self.assertTrue(v in
      [q['comment'] for q in archived_software_release.workflow_history['edit_workflow']])

  @simulateByEditWorkflowMark('SoftwareInstallation_destroyWithSoftwareReleaseArchived')
  def test_no_op_run_software_installation(self):
    preference =  self.portal.portal_preferences.getActiveSystemPreference()
    preference.setPreferredCloudContractEnabled(True)
    self.tic()

    computer, partition = self._makeComputer()
    partition.invalidate()
    partition.markBusy()

    url_string = self.generateNewSoftwareReleaseUrl()
    archived_software_release = self.portal.software_release_module.newContent(
      portal_type='Software Release',
      version='1',
      url_string=url_string,
    )
    archived_software_release.publish()
    archived_software_release.archive()
    self.assertEqual('draft', archived_software_release.getSimulationState())

    software_installation_validated_request_start = self.portal.software_installation_module\
        .newContent(portal_type='Software Installation',
        url_string=url_string,
        aggregate=computer.getRelativeUrl())
    software_installation_validated_request_start.validate()
    software_installation_validated_request_start.requestStart()

    software_installation_validated_request_destroy = self.portal.software_installation_module\
        .newContent(portal_type='Software Installation',
        url_string=url_string,
        aggregate=computer.getRelativeUrl())
    software_installation_validated_request_destroy.validate()
    software_installation_validated_request_destroy.requestStart()
    software_installation_validated_request_destroy.requestDestroy()

    software_installation_invalidated_request_destroy = self.portal.software_installation_module\
        .newContent(portal_type='Software Installation',
        url_string=url_string,
        aggregate=computer.getRelativeUrl())
    software_installation_invalidated_request_destroy.validate()
    software_installation_invalidated_request_destroy.requestStart()
    software_installation_invalidated_request_destroy.requestDestroy()
    software_installation_invalidated_request_destroy.invalidate()
    self.tic()

    # sanity check
    self.assertEqual('validated', software_installation_validated_request_start.getValidationState())
    self.assertEqual('start_requested', software_installation_validated_request_start.getSlapState())
    self.assertEqual('validated', software_installation_validated_request_destroy.getValidationState())
    self.assertEqual('destroy_requested', software_installation_validated_request_destroy.getSlapState())
    self.assertEqual('invalidated', software_installation_invalidated_request_destroy.getValidationState())
    self.assertEqual('destroy_requested', software_installation_invalidated_request_destroy.getSlapState())

    self.stepCallSlaposPdmDestroySoftwareInstallationWithArchivedSoftwareReleaseAlarm()
    self.tic()

    v = 'Visited by SoftwareInstallation_destroyWithSoftwareReleaseArchived'
    self.assertTrue(v in
      [q['comment'] for q in software_installation_validated_request_start.workflow_history['edit_workflow']])
    self.assertFalse(v in
      [q['comment'] for q in software_installation_validated_request_destroy.workflow_history['edit_workflow']])
    self.assertFalse(v in
      [q['comment'] for q in software_installation_invalidated_request_destroy.workflow_history['edit_workflow']])