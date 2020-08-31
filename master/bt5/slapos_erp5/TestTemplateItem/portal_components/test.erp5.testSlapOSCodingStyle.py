# -*- coding: utf8 -*-
##############################################################################
#
# Copyright (c) 2020 Nexedi SA and Contributors. All Rights Reserved.
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

import unittest
from Products.ERP5Type.tests.CodingStyleTestCase import CodingStyleTestCase

from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixin

def makeTestSlapOSCodingStyleTestCase(tested_business_template):
  class TestSlapOSCodingStyle(CodingStyleTestCase, SlapOSTestCaseMixin):
    """Runs CodingStyleTestCase checks on slapos business templates
    """
    def afterSetUp(self):
      CodingStyleTestCase.afterSetUp(self)
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
    if bt.startswith('slapos_'):
      suite.addTest(unittest.makeSuite(makeTestSlapOSCodingStyleTestCase(bt)))

  suite.addTest(unittest.makeSuite(makeTestSlapOSCodingStyleTestCase('slapos_erp5')))
  return suite