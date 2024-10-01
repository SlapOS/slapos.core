portal = context.getPortalObject()
monitor_enabled_category = portal.restrictedTraverse(
  "portal_categories/monitor_scope/enabled", None)

if context.Project_isSupportRequestCreationClosed():
  return

if monitor_enabled_category is not None:
  portal.portal_catalog.searchAndActivate(
    portal_type='Compute Node',
    validation_state='validated',
    monitor_scope__uid=monitor_enabled_category.getUid(),
    follow_up__uid=context.getUid(),
    method_id='ComputeNode_checkMonitoringState',
    activate_kw={'tag': tag}
  )
context.activate(after_tag=tag).getId()
