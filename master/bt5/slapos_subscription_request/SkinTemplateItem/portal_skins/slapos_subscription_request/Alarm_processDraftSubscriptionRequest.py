from DateTime import DateTime
portal = context.getPortalObject()

portal.portal_catalog.searchAndActivate(
  portal_type="Subscription Request",
  validation_state="draft",
  method_id="SubscriptionRequest_verifyPaymentTransaction",
  activity_kw={tag: tag}

)

context.activate(after_tag=tag).getId()
