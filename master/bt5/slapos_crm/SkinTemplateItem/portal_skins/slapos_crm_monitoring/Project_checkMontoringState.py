portal = context.getPortalObject()
monitor_enabled_category = portal.restrictedTraverse(
  "portal_categories/monitor_scope/enabled", None)

if context.Project_isSupportRequestCreationClosed():
  return

if monitor_enabled_category is not None:
  project_uid = context.getUid()
  portal.portal_catalog.searchAndActivate(
    portal_type='Compute Node',
    validation_state='validated',
    monitor_scope__uid=monitor_enabled_category.getUid(),
    follow_up__uid=project_uid,
    method_id='ComputeNode_checkMonitoringState',
    activate_kw={'tag': tag}
  )

  portal.portal_catalog.searchAndActivate(
    portal_type='Instance Tree',
    validation_state='validated',
    follow_up__uid=project_uid,
    method_id='InstanceTree_checkMonitoringState',
    activate_kw = {'tag':tag}
  )

context.activate(after_tag=tag).getId()
