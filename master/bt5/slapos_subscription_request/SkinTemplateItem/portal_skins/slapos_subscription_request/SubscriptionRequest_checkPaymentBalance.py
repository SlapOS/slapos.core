# If Hosting subscription is None, make the request

hosting_subscription = context.getAggregateValue()

# Don't request again if it is already requested.
if hosting_subscription is None:
  context.SubscriptionRequest_processRequest()
  hosting_subscription = context.getAggregateValue()

if hosting_subscription is not None:
  instance = hosting_subscription.getPredecessorValue()

  # This ensure that the user has a valid cloud contract.
  # At this stage he already have a paied invoice for the reservation,
  # so the cloud contact will be just created.

  instance.SoftwareInstance_requestValidationPayment()

  # create a Deduction for his fee
  context.SubscriptionRequest_generateReservationRefoundSalePackingList()

if context.SubscriptionRequest_testPaymentBalance():
  context.confirm()
