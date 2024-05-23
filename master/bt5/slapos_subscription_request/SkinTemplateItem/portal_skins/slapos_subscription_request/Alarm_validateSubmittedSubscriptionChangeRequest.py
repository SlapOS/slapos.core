portal = context.getPortalObject()

portal.portal_catalog.searchAndActivate(
  method_id='SubscriptionChangeRequest_validateIfSubmitted',
  # Project are created only from UI for now
  portal_type=["Subscription Change Request"],
  simulation_state='submitted',
  packet_size=1, # Separate calls to many transactions
  activate_kw={'tag': tag}
)

context.activate(after_tag=tag).getId()
