# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2019 Nexedi SA and Contributors. All Rights Reserved.
#
##############################################################################

from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixin

class TestSlapOSDestroySoftwareInstallationWithArchivedSoftwareReleaseAlarm(SlapOSTestCaseMixin):
  def createComputer(self):
    computer = self.portal.computer_module.template_computer\
        .Base_createCloneDocument(batch_mode=1)
    computer.edit(
      title="computer %s" % (self.new_id, ),
      reference="TESTCOMP-%s" % (self.new_id, ),
      allocation_scope='open/personal',
      capacity_scope='open',
    )
    computer.validate()
    login = computer.newContent(
      portal_type="ERP5 Login",
      reference=computer.getReference()
    )
    login.validate()
    return computer

  def test(self):
    computer = self.createComputer()
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

    # XXX: use the software release

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
