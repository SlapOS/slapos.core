##############################################################################
#
# Copyright (c) 2002-2018 Nexedi SA and Contributors. All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsibility of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# guarantees and support are strongly adviced to contract a Free Software
# Service Company
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
from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixin
from Products.ERP5Type.tests.ERP5TypeFunctionalTestCase import ERP5TypeFunctionalTestCase

class TestSlapOSUIZHHalStyle(SlapOSTestCaseMixin, ERP5TypeFunctionalTestCase):
  foreground = 0
  run_only = "slaposjs_zh_zuite"

  def afterSetUp(self):
    ERP5TypeFunctionalTestCase.afterSetUp(self)
    SlapOSTestCaseMixin.afterSetUp(self)

  def getBusinessTemplateList(self):
    bt5_list = SlapOSTestCaseMixin.getBusinessTemplateList(self)
    bt5_list.extend(
      'slapos_jio_ui_test',
      'slapos_jio_zh_ui_test'
    )
    return bt5_list

def test_suite():
  suite = unittest.TestSuite()
  suite.addTest(unittest.makeSuite(TestSlapOSUIZHHalStyle))
  return suite
