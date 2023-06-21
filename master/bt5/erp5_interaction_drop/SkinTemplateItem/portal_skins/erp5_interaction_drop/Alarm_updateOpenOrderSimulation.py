portal = context.getPortalObject()

portal.portal_catalog.searchAndActivate(
  method_id='OpenOrder_updateSimulation',
  portal_type=portal.getPortalOpenOrderTypeList(),
  validation_state="validated",
  activate_kw={'tag':tag}
  )

# make alarm run once at time
context.activate(after_tag=tag).getId()
