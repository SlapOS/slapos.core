portal = context.getPortalObject()

portal.portal_catalog.searchAndActivate(
  method_id='SubscriptionRequest_validateIfSubmitted',
  method_kw={'activate_kw': {'tag': tag}},
  # Project are created only from UI for now
  portal_type=["Subscription Request"],
  # workgroup request are managed by slapos_subscription_create_workgroup_customer_trade_condition
  destination_section__portal_type=portal.getPortalEntityTypeList(),
  simulation_state='submitted',
  packet_size=1, # Separate calls to many transactions
  activate_kw={'tag': tag, 'priority': 2}
)

context.activate(after_tag=tag).getId()
