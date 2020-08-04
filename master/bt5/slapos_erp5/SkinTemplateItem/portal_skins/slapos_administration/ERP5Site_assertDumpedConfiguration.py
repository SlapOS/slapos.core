portal = context.getPortalObject()

import difflib

def resolveDiff(title, expected_file, found):
  expected = str(expected_file.data)
  return """########################################################################
# %s
########################################################################
%s
########################################################################


""" % (title, '\n'.join(difflib.unified_diff(expected.split("\n"), found.split("\n"))))

if show_all or configuration == "alarm":
  expected_file = portal.expected_alarm_tool_dumped_configuration
  found = portal.ERP5Site_dumpAlarmToolConfiguration()
  print resolveDiff("Alarm Configuration Diff", expected_file, found)

if show_all or configuration == "builder":
  expected_file = portal.expected_builder_dumped_configuration
  found = portal.ERP5Site_dumpBuilderList()
  print resolveDiff("Builder Configuration Diff", expected_file, found)

if show_all or configuration == "bt":
  expected_file = portal.expected_business_template_dumped_configuration
  found = portal.ERP5Site_dumpInstalledBusinessTemplateList(
    ignore_business_template_list=["rapid_space_web_site",
                                   'erp5_ui_test_core',
                                   'slapos_vifib',
                                   'slapos_jio_zh_ui_test',
                                   'slapos_jio_ui_test',
                                   'rapid_space_ui_test'])
  print resolveDiff("Business Template Configuration Diff", expected_file, found)

if show_all or configuration == "order_builder":
  expected_file = portal.expected_order_builder_dumped_configuration
  found = portal.ERP5Site_dumpOrderBuilderList()
  print resolveDiff("Order Builder Configuration Diff", expected_file, found)

if show_all or configuration == "property_sheet":
  expected_file = portal.expected_property_sheet_dumped_configuration
  found = portal.ERP5Site_dumpPropertySheetList(
    ignore_property_sheet_list=["Foo"]
  )
  print resolveDiff("Property Sheet Configuration Diff", expected_file, found)

if show_all or configuration == "skins":
  expected_file = portal.expected_portal_skins_dumped_configuration
  found = portal.ERP5Site_dumpPortalSkinsContent(
    ignore_folder_list=[
      "rapid_space",
      "slapos_vifib",
      "rapid_space_ui_test",
      "slapos_ui_test",
      "slapos_zh_ui_test",
      "erp5_web_renderjs_ui_test_core"
    ],
    ignore_skin_list=[
      "expected_alarm_tool_dumped_configuration",
      "expected_builder_dumped_configuration",
      "expected_business_template_dumped_configuration",
      "expected_order_builder_dumped_configuration",
      "expected_portal_skins_dumped_configuration",
      "expected_portal_type_dumped_configuration",
      "expected_property_sheet_dumped_configuration",
      "expected_role_dumped_configuration",
      "expected_rule_dumped_configuration",
      "expected_skin_property_dumped_configuration",
      "expected_type_actions_dumped_configuration",
      "expected_web_page_module_configuration",
      "expected_workflow_dumped_configuration",
    ]
  )
  print resolveDiff("Skins Configuration Diff", expected_file, found)

if show_all or configuration == "web_content":
  expected_file = portal.expected_web_page_module_configuration
  found = portal.ERP5Site_dumpWebPageModuleContent(
    ignore_string_on_reference_list=["rapid_"])
  print resolveDiff("Web Content Configuration Diff", expected_file, found)

if show_all or configuration == "actions":
  expected_file = portal.expected_type_actions_dumped_configuration
  found = portal.ERP5Site_dumpPortalTypeActionList()
  print resolveDiff("Portal Type Actions Configuration Diff", expected_file, found)

if show_all or configuration == "portal_type":
  expected_file = portal.expected_portal_type_dumped_configuration
  found = portal.ERP5Site_dumpPortalTypeList()
  print resolveDiff("Portal Type Configuration Diff", expected_file, found)

if show_all or configuration == "role":
  expected_file = portal.expected_role_dumped_configuration
  found = portal.ERP5Site_dumpPortalTypeRoleList()
  print resolveDiff("Role Configuration Diff", expected_file, found)

if show_all or configuration == "rule":
  expected_file = portal.expected_rule_dumped_configuration
  found = portal.ERP5Site_dumpRuleTesterList()
  print resolveDiff("Rule Configuration Diff", expected_file, found)

if show_all or configuration == "skin_property":
  expected_file = portal.expected_skin_property_dumped_configuration
  found = portal.ERP5Site_dumpSkinProperty(
    ignore_skin_folder_list=[
      "rapid_space",
      "slapos_vifib",
      "rapid_space_ui_test",
      "slapos_ui_test",
      "slapos_zh_ui_test",
      "erp5_web_renderjs_ui_test_core"
    ]
  )
  print resolveDiff("Skin Property Configuration Diff", expected_file, found)

if show_all or configuration == "workflow":
  expected_file = portal.expected_workflow_dumped_configuration
  found = portal.ERP5Site_dumpWorkflowChain()
  print resolveDiff("Workflow Configuration Diff", expected_file, found)

return printed
