portal = context.getPortalObject()

portal.portal_catalog.searchAndActivate(
  portal_type='Allocation Supply',
  validation_state='validated',
  destination__uid='%',

  method_id='AllocationSupply_invalidateIfInconsistent',
  activate_kw={'tag': tag, 'priority': 5},
)

context.activate(after_tag=tag).getId()
