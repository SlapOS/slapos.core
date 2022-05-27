# -*- coding: utf8 -*-
##############################################################################
#
# Copyright (c) 2020 Nexedi SA and Contributors. All Rights Reserved.
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
from Products.ERP5Type.tests.CodingStyleTestCase import CodingStyleTestCase
from Products.ERP5Type import CodingStyle

from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixin

def makeTestSlapOSCodingStyleTestCase(tested_business_template):
  class TestSlapOSCodingStyle(CodingStyleTestCase, SlapOSTestCaseMixin):
    """Runs CodingStyleTestCase checks on slapos business templates
    """
    def afterSetUp(self):
      CodingStyleTestCase.afterSetUp(self)
      CodingStyle.ignored_skin_id_set.update({
        'InstanceTree_viewConsumptionReport',
        'Person_viewResourceConsumptionReport'})

      CodingStyleTestCase.rebuild_business_template_ignored_path += """

      # Those preferences are changed after the installation, so we skip
      # to check re-export.
      slapos_cloud/PreferenceTemplateItem/portal_preferences/slapos_default_system_preference.xml
      slapos_cloud/PreferenceTemplateItem/portal_preferences/slapos_default_site_preference.xml

      # WebSite is updated after the installation to re-generate the translation data.
      # This list should be reconsider later so we can keep information accurated.
      slapos_jio/PathTemplateItem/web_site_module/hostingjs.xml
      slapos_jio/PathTemplateItem/web_page_module/rjs_gadget_slapos_translation_data_js.js
      slapos_jio/PathTemplateItem/web_page_module/rjs_gadget_slapos_translation_data_js.xml

      # Modified by subprojects during tests
      slapos_crm/PathTemplateItem/sale_trade_condition_module/slapos_ticket_trade_condition.xml
      slapos_payzen/PathTemplateItem/portal_secure_payments/slapos_payzen_test.xml
      """
      SlapOSTestCaseMixin.afterSetUp(self)

    def getBusinessTemplateList(self):
      # include administration for test_PythonSourceCode
      # This method is not used to install business templates in live test, but
      # we define it for CodingStyleTestCase.test_PythonSourceCode
      return ('erp5_administration', )

  return type("TestSlapOSCodingStyle.%s" % tested_business_template,
              (TestSlapOSCodingStyle,),
              {"getTestedBusinessTemplateList": lambda self: (tested_business_template, )})


def test_suite():
  """Generate test to check statically each business template
  """
  suite = unittest.TestSuite()

  from Products.ERP5 import ERP5Site
  portal_templates = ERP5Site.getSite().portal_templates
  bt5 = portal_templates.getInstalledBusinessTemplate("slapos_erp5")
  dependency_list = set(bt5.getTestDependencyList() + bt5.getDependencyList())

  for _, bt in portal_templates.resolveBusinessTemplateListDependency(dependency_list):
    if not bt.startswith('erp5_') or bt.startswith("erp5_interaction_drop"):
      suite.addTest(unittest.makeSuite(makeTestSlapOSCodingStyleTestCase(bt)))

  suite.addTest(unittest.makeSuite(makeTestSlapOSCodingStyleTestCase('slapos_erp5')))
  return suite
