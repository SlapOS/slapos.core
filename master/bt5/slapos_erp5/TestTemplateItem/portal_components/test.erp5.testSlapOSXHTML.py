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
