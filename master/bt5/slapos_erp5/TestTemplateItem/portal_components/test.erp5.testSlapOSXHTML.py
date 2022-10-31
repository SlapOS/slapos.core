# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (C) 2013-2019  Nexedi SA and Contributors.
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
"""Tests all forms.
"""
import unittest

from Products.ERP5.tests import testXHTML
from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixin

class TestSlapOSXHTML(SlapOSTestCaseMixin, testXHTML.TestXHTML):

  # some forms have intentionally empty listbox selections like RSS generators
  JSL_IGNORE_SKIN_LIST = ('erp5_code_mirror', 'erp5_ckeditor',
                          'erp5_fckeditor', 'erp5_ui_test_core',
                          'erp5_jquery', 'erp5_jquery_ui',
                          'erp5_svg_editor', 'erp5_xinha_editor',
                          'erp5_monaco_editor', 'erp5_slideshow_core',
                          'erp5_run_my_doc', 'erp5_web_renderjs',
                          'erp5_corporate_identity',
                          'erp5_corporate_identity_web',
                          'erp5_notebook', 'erp5_officejs_notebook',
                          'erp5_web_js_style_ui', 'slapos_hal_json_style')
  def afterSetUp(self):
    SlapOSTestCaseMixin.afterSetUp(self)
    # Live tests all uses the same request. For now we remove cell from
    # previous test that can cause problems in this test.
    self.portal.REQUEST.other.pop('cell', None)

def test_suite():
  from Products.ERP5 import ERP5Site
  portal_templates = ERP5Site.getSite().portal_templates
  dependency_list = portal_templates.getInstalledBusinessTemplate(
      "slapos_erp5").getTestDependencyList()
  bt5_list = [p[1] for p in portal_templates.resolveBusinessTemplateListDependency(
      dependency_list)]
  testXHTML.addTestMethodDynamically(
    TestSlapOSXHTML,
    testXHTML.validator,
    bt5_list)

  suite = unittest.TestSuite()
  suite.addTest(unittest.makeSuite(TestSlapOSXHTML))
  return suite
