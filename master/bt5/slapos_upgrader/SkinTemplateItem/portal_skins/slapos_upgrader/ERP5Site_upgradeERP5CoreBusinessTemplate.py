portal = context.getPortalObject()
template_tool = portal.portal_templates

template_tool.updateRepositoryBusinessTemplateList(
  template_tool.getRepositoryList())

method_kw = {'bt5_list': ['erp5_core'],
             'deprecated_after_script_dict': None,
             'deprecated_reinstall_set': None,
             'dry_run': False,
             'delete_orphaned': False,
             'keep_bt5_id_set': [],
             'update_catalog': False}


template_tool.upgradeSite(**method_kw)

if skip_upgrader:
  return "Skipped to upgrade slapos_upgrader"

# Use activities to ensure that it done on another transaction
tag = "upgrader:ERP5Site_upgradeUpgraderBusinessTemplate"
template_tool.activate(
  tag=tag).ERP5Site_upgradeUpgraderBusinessTemplate()

if skip_alarm:
  return "Skipped to call portal_alarms.promise_check_upgrade.activeSense"
portal.portal_alarms.promise_check_upgrade.activate(
  tag="upgrader:promise_check_upgrade", after_tag=tag).activeSense()
