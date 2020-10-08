from DateTime import DateTime
portal = context.getPortalObject()

portal.portal_catalog.searchAndActivate(
  portal_type="Subscription Request",
  simulation_state="stopped",
  method_id="SubscriptionRequest_processStopped",
  activity_kw={tag: tag}

)

context.activate(after_tag=tag).getId()
