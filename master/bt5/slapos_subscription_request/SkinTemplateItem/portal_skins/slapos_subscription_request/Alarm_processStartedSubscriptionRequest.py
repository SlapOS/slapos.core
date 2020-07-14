from DateTime import DateTime
portal = context.getPortalObject()

portal.portal_catalog.searchAndActivate(
  portal_type="Subscription Request",
  simulation_state="started",
  method_id="SubscriptionRequest_processStarted",
  activity_kw={tag: tag}

)

context.activate(after_tag=tag).getId()
