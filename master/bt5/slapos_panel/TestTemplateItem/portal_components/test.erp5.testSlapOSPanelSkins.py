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

from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixinWithAbort

def getFakeSlapState():
  return "destroy_requested"

class TestPanelSkinsMixin(SlapOSTestCaseMixinWithAbort):

  def afterSetUp(self):
    SlapOSTestCaseMixinWithAbort.afterSetUp(self)
    self.project = self.addProject()

 
class TestSupportRequestModule_getRssFeedUrl(TestPanelSkinsMixin):

  def testSupportRequestModule_getRssFeedUrl(self):
    module = self.portal.support_request_module
    self.assertRaises(ValueError, module.SupportRequestModule_getRssFeedUrl)
    person = self.makePerson(self.project, user=1)
    self.addProjectProductionManagerAssignment(person, self.project)
    self.tic()

    self.login(person.getUserId())

    # Fail if not on website context.
    self.assertRaises(ValueError, module.SupportRequestModule_getRssFeedUrl)

    module = self.portal.web_site_module.slapos_master_panel.support_request_module
    url = module.SupportRequestModule_getRssFeedUrl()
    self.assertIn('feed', url)
    self.assertIn(
      self.portal.web_site_module.slapos_master_panel.feed.absolute_url(), url)
    self.assertIn('access_token_secret', url)
    self.assertIn('access_token=', url)

    self.tic()
    self.assertEqual(url, module.SupportRequestModule_getRssFeedUrl())







    