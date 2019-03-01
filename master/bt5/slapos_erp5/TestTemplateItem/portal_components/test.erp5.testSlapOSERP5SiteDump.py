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
    issue_count = 0
    for dump, filename in [
        ('ERP5Site_dumpAlarmToolConfiguration', 'expected_alarm_tool_dumped_configuration'),
        ('ERP5Site_dumpBuilderList', 'expected_builder_dumped_configuration'),
        ('ERP5Site_dumpInstalledBusinessTemplateList', 'expected_business_template_dumped_configuration'),
        ('ERP5Site_dumpOrderBuilderList', 'expected_order_builder_dumped_configuration'),
        ('ERP5Site_dumpPortalTypeActionList', 'expected_type_actions_dumped_configuration'),
        ('ERP5Site_dumpPortalTypeList', 'expected_portal_type_dumped_configuration'),
        ('ERP5Site_dumpPortalTypeRoleList', 'expected_role_dumped_configuration'),
        ('ERP5Site_dumpPortalSkinsContent', 'expected_portal_skins_dumped_configuration'),
        ('ERP5Site_dumpPropertySheetList', 'expected_property_sheet_dumped_configuration'),
        ('ERP5Site_dumpRuleTesterList', 'expected_rule_dumped_configuration'),
        ('ERP5Site_dumpSkinProperty', 'expected_skin_property_dumped_configuration'),
        ('ERP5Site_dumpWorkflowChain', 'expected_workflow_dumped_configuration'),
      ]:
      ZopeTestCase._print('\n')
      try:
        location = self.write('%s' % filename, getattr(self.portal, dump)())
      except Exception:
        ZopeTestCase._print('Problem with %s\n' % dump)
        issue_count += 1
      else:
        ZopeTestCase._print('Stored dump %s in %s\n' % (dump, location))
    self.assertEqual(0, issue_count)