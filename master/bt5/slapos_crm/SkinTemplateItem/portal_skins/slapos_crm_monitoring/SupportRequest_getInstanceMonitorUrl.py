support_request = context

hosting_subscription = support_request.getAggregateValue(portal_type="Hosting Subscription")
if hosting_subscription is None:
  return

instance = None
for possible_instance in hosting_subscription.getPredecessorValueList():
  if possible_instance.getSlapState() != 'destroy_requested':
    instance = possible_instance
    break
if instance is None:
  return

parameter_dict = instance.getConnectionXmlAsDict()
return parameter_dict.get('monitor-setup-url', None)
