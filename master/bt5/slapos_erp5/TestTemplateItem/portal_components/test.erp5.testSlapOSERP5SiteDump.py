# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2012 Nexedi SA and Contributors. All Rights Reserved.
#
##############################################################################

from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixin

import os
from Testing import ZopeTestCase

class TestSlapOSDump(SlapOSTestCaseMixin):
  def write(self, name, output):
    path = os.path.join(os.environ['INSTANCE_HOME'], name)
    with open(path, 'w') as f:
      f.write(output)
    return path

  def test(self):
    self.beforeDumpExpectedConfiguration()
    issue_count = 0
    for dump, filename, kwargs in [
        ('ERP5Site_dumpAlarmToolConfiguration', 'expected_alarm_tool_dumped_configuration', None),
        ('ERP5Site_dumpBuilderList', 'expected_builder_dumped_configuration', None),
        ('ERP5Site_dumpInstalledBusinessTemplateList', 'expected_business_template_dumped_configuration',
             {'ignore_business_template_list': ["erp5_ui_test_core"]}),
        ('ERP5Site_dumpPortalTypeActionList', 'expected_type_actions_dumped_configuration', None),
        ('ERP5Site_dumpPortalTypeList', 'expected_portal_type_dumped_configuration', None),
        ('ERP5Site_dumpPortalTypeRoleList', 'expected_role_dumped_configuration', None),
        ('ERP5Site_dumpPortalSkinsContent', 'expected_portal_skins_dumped_configuration', None),
        ('ERP5Site_dumpPropertySheetList', 'expected_property_sheet_dumped_configuration', None),
        ('ERP5Site_dumpRuleTesterList', 'expected_rule_dumped_configuration', None),
        ('ERP5Site_dumpSkinProperty', 'expected_skin_property_dumped_configuration', None),
        ('ERP5Site_dumpWebPageModuleContent', 'expected_web_page_module_configuration', None),
        ('ERP5Site_dumpWorkflowChain', 'expected_workflow_dumped_configuration', None),
      ]:
      ZopeTestCase._print('\n')
      try:
        if kwargs is None:
          location = self.write('%s' % filename, getattr(self.portal, dump)())
        else:
          location = self.write('%s' % filename, getattr(self.portal, dump)(**kwargs))
      except Exception:
        ZopeTestCase._print('Problem with %s\n' % dump)
        issue_count += 1
      else:
        ZopeTestCase._print('Stored dump %s in %s\n' % (dump, location))
    self.assertEqual(0, issue_count)

  def test_save_and_assert(self):
    self.beforeDumpExpectedConfiguration()
    self.assertRaises(ValueError, self.portal.ERP5Site_assertDumpedConfiguration)
    msg = self.portal.ERP5Site_saveDumpedConfiguration()
    self.assertEqual('', self.portal.ERP5Site_assertDumpedConfiguration())

    ZopeTestCase._print('\n')
    filename = 'erp5_dumped_configuration'
    try:
      location = self.write('%s' % filename, msg)
    except Exception:
      ZopeTestCase._print(
        'Problem with %s\n' % filename)
    else:
      ZopeTestCase._print(
        'Stored dump ERP5Site_saveDumpedConfiguration in %s\n' % (location,))
    
