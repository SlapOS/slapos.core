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

from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixin
from erp5.component.test.testSlapOSAccountingAlarm import simulateByEditWorkflowMark

class TestSlapOSDestroySoftwareInstallationWithArchivedSoftwareReleaseAlarm(SlapOSTestCaseMixin):

  launch_caucase = 1
  
  def createInstance(self, url_string):
    instance_tree = self.portal.instance_tree_module\
        .template_instance_tree.Base_createCloneDocument(batch_mode=1)
    instance_tree.edit(
    )
    instance_tree.validate()
    instance_tree.edit(
        title=self.generateNewSoftwareTitle(),
        reference="TESTHS-%s" % self.generateNewId(),
    )
    request_kw = dict(
      software_release=url_string,
      software_type=self.generateNewSoftwareType(),
      instance_xml=self.generateSafeXml(),
      sla_xml=self.generateSafeXml(),
      shared=False,
      software_title=instance_tree.getTitle(),
      state='started'
    )
    instance_tree.requestStart(**request_kw)
    instance_tree.requestInstance(**request_kw)

    instance = instance_tree.getSuccessorValue()
    self.tic()
    return instance

  def test(self):
    preference =  self.portal.portal_preferences.getActiveSystemPreference()
    preference.setPreferredCloudContractEnabled(True)
    self.tic()
    compute_node, partition = self._makeComputeNode()
    compute_node.setUpgradeScope('auto')
    archived_url_string = self.generateNewSoftwareReleaseUrl()
    # create software release
    archived_software_release = self.portal.software_release_module.newContent(
      portal_type='Software Release',
      version='1',
      url_string=archived_url_string
    )
    archived_software_release.publish()
    archived_software_release.archive()
    # install an software release
    archived_software_installation = self.portal.software_installation_module\
        .newContent(portal_type='Software Installation',
        url_string=archived_url_string,
        aggregate=compute_node.getRelativeUrl())
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
    # install an software release
    archived_used_software_installation = self.portal.software_installation_module\
        .newContent(portal_type='Software Installation',
        url_string=archived_used_url_string,
        aggregate=compute_node.getRelativeUrl())
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
    # install an software release
    published_software_installation = self.portal.software_installation_module\
        .newContent(portal_type='Software Installation',
        url_string=published_url_string,
        aggregate=compute_node.getRelativeUrl())
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
    
    # second run, but it is still not reported that software installation is destroyed
    self.stepCallSlaposPdmDestroySoftwareInstallationWithArchivedSoftwareReleaseAlarm()
    self.tic()
    
    self.assertEqual('start_requested', published_software_installation.getSlapState())
    self.assertEqual('validated', archived_used_software_installation.getValidationState())
    self.assertEqual('start_requested', archived_used_software_installation.getSlapState())

  def test_manual_upgrade_scope(self):
    preference =  self.portal.portal_preferences.getActiveSystemPreference()
    preference.setPreferredCloudContractEnabled(True)
    self.tic()
    compute_node, partition = self._makeComputeNode()
    compute_node.setUpgradeScope('confirmation')
    archived_url_string = self.generateNewSoftwareReleaseUrl()
    # create software release
    archived_software_release = self.portal.software_release_module.newContent(
      portal_type='Software Release',
      version='1',
      url_string=archived_url_string
    )
    archived_software_release.publish()
    archived_software_release.archive()
    # install an software release
    archived_software_installation = self.portal.software_installation_module\
        .newContent(portal_type='Software Installation',
        url_string=archived_url_string,
        aggregate=compute_node.getRelativeUrl())
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
    # install an software release
    archived_used_software_installation = self.portal.software_installation_module\
        .newContent(portal_type='Software Installation',
        url_string=archived_used_url_string,
        aggregate=compute_node.getRelativeUrl())
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
    # install an software release
    published_software_installation = self.portal.software_installation_module\
        .newContent(portal_type='Software Installation',
        url_string=published_url_string,
        aggregate=compute_node.getRelativeUrl())
    published_software_installation.validate()
    published_software_installation.requestStart()
    self.tic()
    
    # as Compute Node is manually managed, nothing happens
    self.stepCallSlaposPdmDestroySoftwareInstallationWithArchivedSoftwareReleaseAlarm()
    self.tic()
    self.assertEqual('start_requested', archived_software_installation.getSlapState())
    self.assertEqual('validated', archived_software_installation.getValidationState())

    self.assertEqual('start_requested', published_software_installation.getSlapState())
    self.assertEqual('validated', published_software_installation.getValidationState())

    self.assertEqual('start_requested', archived_used_software_installation.getSlapState())
    self.assertEqual('validated', archived_used_software_installation.getValidationState())

  @simulateByEditWorkflowMark('SoftwareRelease_findAndDestroySoftwareInstallation')
  def test_no_op_run_software_release(self):
    archived_software_release = self.portal.software_release_module.newContent(
      portal_type='Software Release',
      version='1',
      url_string=self.generateNewSoftwareReleaseUrl(),
    )
    archived_software_release.publish()
    archived_software_release.archive()

    archived_cleaned_software_release = self.portal.software_release_module.newContent(
      portal_type='Software Release',
      version='1',
      url_string=self.generateNewSoftwareReleaseUrl(),
    )
    archived_cleaned_software_release.publish()
    archived_cleaned_software_release.archive()

    published_software_release = self.portal.software_release_module.newContent(
      portal_type='Software Release',
      version='1',
      url_string=self.generateNewSoftwareReleaseUrl(),
    )
    published_software_release.publish()
    self.tic()

    self.stepCallSlaposPdmDestroySoftwareInstallationWithArchivedSoftwareReleaseAlarm()
    self.tic()

    v = 'Visited by SoftwareRelease_findAndDestroySoftwareInstallation'
    self.assertNotIn(v,
      [q['comment'] for q in published_software_release.workflow_history['edit_workflow']])
    self.assertIn(v,
      [q['comment'] for q in archived_cleaned_software_release.workflow_history['edit_workflow']])
    self.assertIn(v,
      [q['comment'] for q in archived_software_release.workflow_history['edit_workflow']])

  @simulateByEditWorkflowMark('SoftwareInstallation_destroyWithSoftwareReleaseArchived')
  def test_no_op_run_software_installation(self):
    preference =  self.portal.portal_preferences.getActiveSystemPreference()
    preference.setPreferredCloudContractEnabled(True)
    self.tic()

    compute_node, partition = self._makeComputeNode()
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

    software_installation_validated_request_start = self.portal.software_installation_module\
        .newContent(portal_type='Software Installation',
        url_string=url_string,
        aggregate=compute_node.getRelativeUrl())
    software_installation_validated_request_start.validate()
    software_installation_validated_request_start.requestStart()

    software_installation_validated_request_destroy = self.portal.software_installation_module\
        .newContent(portal_type='Software Installation',
        url_string=url_string,
        aggregate=compute_node.getRelativeUrl())
    software_installation_validated_request_destroy.validate()
    software_installation_validated_request_destroy.requestStart()
    software_installation_validated_request_destroy.requestDestroy()

    software_installation_invalidated_request_destroy = self.portal.software_installation_module\
        .newContent(portal_type='Software Installation',
        url_string=url_string,
        aggregate=compute_node.getRelativeUrl())
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
    self.assertIn(v,
      [q['comment'] for q in software_installation_validated_request_start.workflow_history['edit_workflow']])
    self.assertNotIn(v,
      [q['comment'] for q in software_installation_validated_request_destroy.workflow_history['edit_workflow']])
    self.assertNotIn(v,
      [q['comment'] for q in software_installation_invalidated_request_destroy.workflow_history['edit_workflow']])