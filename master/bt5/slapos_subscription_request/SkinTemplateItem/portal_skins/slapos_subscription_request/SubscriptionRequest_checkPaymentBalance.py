# If Hosting subscription is None, make the request

context.SubscriptionRequest_processRequest()

# Don't continue if instance wasnt there.
if context.getAggregate() is None:
  return

#if context.SubscriptionRequest_testPaymentBalance():
# context.confirm()
