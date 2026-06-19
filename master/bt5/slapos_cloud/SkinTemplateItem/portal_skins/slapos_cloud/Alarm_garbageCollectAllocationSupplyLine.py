portal = context.getPortalObject()

portal.portal_catalog.searchAndActivate(
  portal_type='Allocation Supply Line',
  validation_state='deleted',
  group_by=['parent_uid'],

  method_id='AllocationSupplyLine_tryToGarbageCollect',
  activate_kw={'tag': tag},
)

context.activate(after_tag=tag).getId()
