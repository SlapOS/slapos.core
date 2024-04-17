# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2012 Vifib SA and Contributors. All Rights Reserved.
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

from .testSlapOSMixin import testSlapOSMixin
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
    self.assertEqual(alarm.getLastActiveProcess().getResultList(), [])

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
    self.assertEqual(
      error_list, [],
      msg="The following Portal Type classes could not be loaded (see zLOG.log): %r" % error_list)


def test_suite():
  suite = unittest.TestSuite()
  suite.addTest(unittest.makeSuite(TestUpgradeInstanceWithOldDataFs))
  return suite
