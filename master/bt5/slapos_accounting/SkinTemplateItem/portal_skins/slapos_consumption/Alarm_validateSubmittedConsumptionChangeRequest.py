portal = context.getPortalObject()

portal.portal_catalog.searchAndActivate(
  method_id='ConsumptionChangeRequest_validateIfSubmitted',
  method_kw={'activate_kw': {'tag': tag}},
  # Project are created only from UI for now
  portal_type=["Consumption Change Request"],
  simulation_state='submitted',
  activate_kw={'tag': tag, 'priority': 2}
)

context.activate(after_tag=tag).getId()
