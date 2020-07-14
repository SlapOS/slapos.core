hosting_subscription = context.getAggregateValue()

if hosting_subscription is not None and \
    hosting_subscription.getSlapState() == "destroy_requested":

  context.stop()
