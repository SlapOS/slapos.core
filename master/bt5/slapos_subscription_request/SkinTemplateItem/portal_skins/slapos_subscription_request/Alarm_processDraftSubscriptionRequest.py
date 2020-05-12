from DateTime import DateTime
portal = context.getPortalObject()

portal.portal_catalog.searchAndActivate(
  portal_type="Subscription Request",
  simulation_state="draft",
  method_id="SubscriptionRequest_verifyReservationPaymentTransaction",
  activity_kw={tag: tag}

)

context.activate(after_tag=tag).getId()
