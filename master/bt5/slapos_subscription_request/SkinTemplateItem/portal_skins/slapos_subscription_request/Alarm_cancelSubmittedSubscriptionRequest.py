portal = context.getPortalObject()

portal.portal_catalog.searchAndActivate(
  method_id='SubscriptionRequest_cancelIfSubmitted',
  # Project are created only from UI for now
  portal_type=["Subscription Request"],
  simulation_state='submitted',
  packet_size=1, # Separate calls to many transactions
  activate_kw={'tag': tag}
)

context.activate(after_tag=tag).getId()
