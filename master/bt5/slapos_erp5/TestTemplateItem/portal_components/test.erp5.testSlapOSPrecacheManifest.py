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
from erp5.component.test.SlapOSTestCaseMixin import \
  SlapOSTestCaseMixinWithAbort


class TestSlapOSHostingJSPrecacheManifestList(SlapOSTestCaseMixinWithAbort):

  manifest_script_id = 'WebSection_getHostingJSPrecacheManifestList'

  def isPublishedWebPage(self, reference):
    return self.web_site.getDocumentValue(reference) is not None

  def isPath(self, reference):
    return self.portal.restrictedTraverse(reference, None) is not None

  def test(self):
    self.web_site = self.portal.web_site_module.renderjs_oss
    self.changeSkin('Hal')
    manifest_script = getattr(self.web_site, self.manifest_script_id)
    failure_list = []
    self.logout()

    for _entry in manifest_script():
      # Normalize url
      entry = _entry.split('?')[0]
      if not (self.isPublishedWebPage(entry) or \
                self.isPath(entry)):
        failure_list.append(entry)

    self.assertEqual(failure_list, [])


class TestSlapOSRenderJSRunnerAccessPagePrecacheManifestList(
    TestSlapOSHostingJSPrecacheManifestList):
  manifest_script_id = 'WebSection_getRenderJSRunnerAccessPagePrecacheManifestList'

class TestSlapOSMonacoEditorPrecacheManifestList(
    TestSlapOSHostingJSPrecacheManifestList):
  manifest_script_id = 'WebSection_getMonacoEditorPrecacheManifestList'

class TestSlapOSJsonEditorPrecacheManifestList(
    TestSlapOSHostingJSPrecacheManifestList):
  manifest_script_id = 'WebSection_getJsonEditorPrecacheManifestList'