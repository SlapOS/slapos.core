portal = context.getPortalObject()

activate_kw = {'tag': tag, 'priority': 2}

portal.portal_catalog.searchAndActivate(
  portal_type='Sale Trade Condition Change Request',
  simulation_state='submitted',

  method_id='SaleTradeConditionChangeRequest_validateIfSubmitted',
  method_kw={'activate_kw': activate_kw},
  # Limit activity number, to limit the number of concurrent changes
  # (to not have conflicting STC)
  activity_count=1,
  packet_size=1,
  activate_kw=activate_kw
)
context.activate(after_tag=tag).getId()
