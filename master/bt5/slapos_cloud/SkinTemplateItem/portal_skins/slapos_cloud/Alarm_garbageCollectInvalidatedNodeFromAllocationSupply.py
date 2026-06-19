portal = context.getPortalObject()

portal.portal_catalog.searchAndActivate(
  portal_type='Allocation Supply',
  aggregate__validation_state='invalidated',

  method_id='AllocationSupply_tryToGarbageCollectInvalidatedNode',
  activate_kw={'tag': tag},
)

context.activate(after_tag=tag).getId()
