portal = context.getPortalObject()

return portal.portal_catalog(
    portal_type='Compute Node',
    default_allocation_scope_uid=[
      portal.restrictedTraverse("portal_categories/allocation_scope/open").getUid()
    ],
    validation_state="validated",
    sort_on=(("title", "ASC" ),)
  )
