##############################################################################
#
# Copyright (c) 2022 Nexedi SA and Contributors. All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsibility of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# guarantees and support are strongly adviced to contract a Free Software
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
##############################################################################

import unittest
from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixin
from Products.ERP5Type.tests.ERP5TypeFunctionalTestCase import ERP5TypeFunctionalTestCase

class TestSlapOSRenderJSOSSUIHalStyle(SlapOSTestCaseMixin, ERP5TypeFunctionalTestCase):
  foreground = 0
  run_only = "slapos_renderjs_oss_zuite"

  def afterSetUp(self):
    ERP5TypeFunctionalTestCase.afterSetUp(self)
    SlapOSTestCaseMixin.afterSetUp(self)
    # Ensuring the default available language is "en" for English UI test
    self.portal.web_site_module.renderjs_oss.setDefaultAvailableLanguage('en')
    # fix consistency to update translation
    self.portal.web_site_module.renderjs_oss.fixConsistency()
    self.tic()

def test_suite():
  suite = unittest.TestSuite()
  suite.addTest(unittest.makeSuite(TestSlapOSRenderJSOSSUIHalStyle))
  return suite
