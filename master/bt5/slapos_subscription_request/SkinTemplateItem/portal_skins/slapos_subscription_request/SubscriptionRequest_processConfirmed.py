hosting_subscription = context.getAggregateValue()

if hosting_subscription is None:
  # Probably we should raise here
  return

request_kw = dict(
      software_release=hosting_subscription.getUrlString(),
      software_title=hosting_subscription.getTitle(),
      software_type=hosting_subscription.getSourceReference(),
      instance_xml=hosting_subscription.getTextContent(),
      sla_xml=hosting_subscription.getSlaXml(),
      shared=hosting_subscription.isRootSlave()
)

if not context.SubscriptionRequest_testPaymentBalance():
  # Payment isn't paid by the user, so we stop the instance and wait
  if hosting_subscription.getSlapState() == "start_requested":
    person = hosting_subscription.getDefaultDestinationSectionValue()
    person.requestSoftwareInstance(state='stopped', **request_kw)
  return

if hosting_subscription.getSlapState() == "stop_requested":
  person = hosting_subscription.getDefaultDestinationSectionValue()
  person.requestSoftwareInstance(state='started', **request_kw)
  # Return to because it is useless continue right the way.
  return

if not context.SubscriptionRequest_verifyInstanceIsAllocated():
  # Only continue if instance is ready
  return

if context.SubscriptionRequest_notifyInstanceIsReady():
  context.start()
