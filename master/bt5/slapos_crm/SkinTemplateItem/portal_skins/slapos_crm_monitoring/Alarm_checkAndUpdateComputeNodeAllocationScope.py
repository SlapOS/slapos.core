portal = context.getPortalObject()

category_public = portal.restrictedTraverse("portal_categories/allocation_scope/open/public", None)
category_subscription = portal.restrictedTraverse("portal_categories/allocation_scope/open/subscription", None)

if category_public is not None:
  portal.portal_catalog.searchAndActivate(
    portal_type='Compute Node',
    default_allocation_scope_uid=[category_public.getUid(), category_subscription.getUid()],
    validation_state="validated",
    method_id='ComputeNode_checkAndUpdateAllocationScope',
    activate_kw={'tag': tag}
  )

context.activate(after_tag=tag).getId()
