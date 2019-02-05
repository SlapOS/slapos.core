if event_value is None:
  event_value = context

support_request = event_value.getFollowUpValue()
hosting_subscription = support_request.getAggregateValue()
if hosting_subscription is None:
  return {}

owner = hosting_subscription.getDestinationSectionValue()

return {
  "owner_name": owner.getFirstName(),
  "instance_name": hosting_subscription.getTitle(),
}
