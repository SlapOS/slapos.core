portal = context.getPortalObject()
monitor_enabled_category = portal.restrictedTraverse(
  "portal_categories/monitor_scope/enabled", None)

portal = context.getPortalObject()
portal.portal_catalog.searchAndActivate(
    portal_type='Compute Node',
    validation_state='validated',
    method_id='ComputeNode_checkProjectMontoringState',
    monitor_scope__uid=monitor_enabled_category.getUid(),
    group_by=['follow_up_uid'],
    method_kw={'tag': tag},
    activate_kw={'tag': tag}
  )
context.activate(after_tag=tag).getId()
