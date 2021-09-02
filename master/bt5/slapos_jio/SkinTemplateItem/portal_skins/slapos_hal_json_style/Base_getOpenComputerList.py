portal = context.getPortalObject()

category_public = portal.restrictedTraverse("portal_categories/allocation_scope/open/public", None)
category_friend = portal.restrictedTraverse("portal_categories/allocation_scope/open/friend", None)
category_personal = portal.restrictedTraverse("portal_categories/allocation_scope/open/personal", None)

return portal.portal_catalog(
    portal_type='Computer',
    default_allocation_scope_uid=[
      category_public.getUid(),
      category_friend.getUid(),
      category_personal.getUid()],
    validation_state="validated",
  )
