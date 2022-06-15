portal = context.getPortalObject()

if portal.ERP5Site_isSupportRequestCreationClosed():
  # Stop process alarm if there are too many tickets
  return

monitor_enabled_category = portal.restrictedTraverse(
  "portal_categories/monitor_scope/enabled", None)

if monitor_enabled_category is not None:
  portal.portal_catalog.searchAndActivate(
    portal_type='Compute Node',
    validation_state='validated',
    monitor_scope__uid=monitor_enabled_category.getUid(),
    method_id='ComputeNode_checkState',
    activate_kw={'tag':tag}
  )

context.activate(after_tag=tag).getId()
