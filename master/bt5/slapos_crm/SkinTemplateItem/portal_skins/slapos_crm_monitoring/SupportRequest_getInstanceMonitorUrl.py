support_request = context

hosting_subscription = support_request.getAggregateValue(portal_type="Hosting Subscription")
if hosting_subscription is None:
  return

instance = hosting_subscription.getPredecessorValue()
if instance is None or instance.getSlapState() == 'destroy_requested':
  return

parameter_dict = instance.getConnectionXmlAsDict()
return parameter_dict.get('monitor-setup-url', None)
