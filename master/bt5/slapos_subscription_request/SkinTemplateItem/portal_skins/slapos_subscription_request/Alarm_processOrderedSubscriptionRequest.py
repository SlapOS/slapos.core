from DateTime import DateTime
portal = context.getPortalObject()

portal.portal_catalog.searchAndActivate(
  portal_type="Subscription Request",
  simulation_state="ordered",
  method_id="SubscriptionRequest_processOrdered",
  activity_kw={tag: tag}

)

context.activate(after_tag=tag).getId()
