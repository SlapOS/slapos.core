portal = context.getPortalObject()

active_process = context.newActiveProcess().getRelativeUrl()

# Closed compute_nodes like this might contains unremoved instances hanging there.
category_close_forever = portal.restrictedTraverse(
    "portal_categories/allocation_scope/close/forever", None)
category_close_outdated = portal.restrictedTraverse(
  "portal_categories/allocation_scope/close/outdated", None)


return portal.portal_catalog.searchAndActivate(
    method_kw=dict(fixit=fixit, active_process=active_process),
    method_id="ComputeNode_checkInstanceOnCloseAllocation",
    portal_type='Compute Node',
    default_allocation_scope_uid=[category_close_forever.getUid(), category_close_outdated.getUid()],
    validation_state="validated",
    activite_kw={"tag": tag}  )
