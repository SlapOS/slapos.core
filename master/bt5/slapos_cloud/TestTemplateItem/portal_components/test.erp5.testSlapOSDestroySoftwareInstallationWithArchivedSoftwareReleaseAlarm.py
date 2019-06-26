# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2019 Nexedi SA and Contributors. All Rights Reserved.
#
##############################################################################

from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixin

class TestSlapOSDestroySoftwareInstallationWithArchivedSoftwareReleaseAlarm(SlapOSTestCaseMixin):
  def test(self):
    self.fail('Typical case')

  def test_software_release_to_cleanup(self):
    self.fail('SR to cleanup')

  def test_no_op_run(self):
    self.fail('Prove that alarm does not spawn activities in case if all SRs are cleaned')
