portal = context.getPortalObject()

portal.portal_catalog.searchAndActivate(
  method_id='OpenOrder_updateSimulation',
  portal_type=portal.getPortalOpenOrderTypeList(),
  validation_state="validated",
  # This alarm bruteforce checking all documents,
  # without changing them directly.
  # Increase priority to not block other activities
  activate_kw={'tag':tag, 'priority': 2}
  )

# make alarm run once at time
context.activate(after_tag=tag).getId()
