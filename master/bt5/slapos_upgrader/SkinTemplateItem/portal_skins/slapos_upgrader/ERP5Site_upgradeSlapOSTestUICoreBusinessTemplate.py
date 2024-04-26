template_tool = context.getPortalObject().portal_templates

template_tool.updateRepositoryBusinessTemplateList(
  template_tool.getRepositoryList())

method_kw = {'bt5_list': ['erp5_ui_test_core', 'slapos_panel_ui_test', 'slapos_parameter_ui_test'],
             'deprecated_after_script_dict': None,
             'deprecated_reinstall_set': None,
             'dry_run': False,
             'delete_orphaned': False,
             'keep_bt5_id_set': [],
             'update_catalog': False}


template_tool.upgradeSite(**method_kw)
