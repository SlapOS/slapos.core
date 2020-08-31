# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2012 Nexedi SA and Contributors. All Rights Reserved.
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

from testSlapOSMixin import testSlapOSMixin
import unittest

class TestUpgradeInstanceWithOldDataFs(testSlapOSMixin):
  def afterSetUp(self):
    # Do nothing as all work is done on the saved testSlapOSMixin already
    # When save the data.fs
    pass

  def getBusinessTemplateList(self):
    # we dont need bt5 as this test is supposed to run only as --load
    return ['erp5_core']

  def testUpgrade(self):
    if not self.portal.portal_templates.getRepositoryList():
      self.setupAutomaticBusinessTemplateRepository(
        searchable_business_template_list=["erp5_core", "erp5_base",
                                           "slapos_erp5", "erp5_slapos_tutorial"])

    alarm = self.portal.portal_alarms.promise_check_upgrade
    alarm.solve()
    self.tic()
    self.assertEquals(alarm.getLastActiveProcess().getResultList(), [])

    bt5_list = self.portal.portal_templates.getInstalledBusinessTemplateTitleList()
    self.assertTrue('slapos_erp5' in bt5_list, bt5_list)

    # Make sure that *all* Portal Type can be loaded after upgrade
    import erp5.portal_type
    from Products.ERP5Type.dynamic.lazy_class import ERP5BaseBroken
    error_list = []
    for portal_type_obj in self.portal.portal_types.listTypeInfo():
      portal_type_id = portal_type_obj.getId()
      portal_type_class = getattr(erp5.portal_type, portal_type_id)
      portal_type_class.loadClass()
      if issubclass(portal_type_class, ERP5BaseBroken):
        error_list.append(portal_type_id)
    self.assertEquals(
      error_list, [],
      msg="The following Portal Type classes could not be loaded (see zLOG.log): %r" % error_list)


def test_suite():
  suite = unittest.TestSuite()
  suite.addTest(unittest.makeSuite(TestUpgradeInstanceWithOldDataFs))
  return suite
