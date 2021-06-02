if context.getSimulationState() != "ordered":
  # Skip if the instance isn't ordered anymore
  return

hosting_subscription = context.getAggregateValue()

# Don't request again if it is already requested.
if hosting_subscription is None:
  context.SubscriptionRequest_processRequest()
  # Don't perform everything on the same transaction
  return "Skipped (Instance Requested)"

if hosting_subscription is not None:
  if hosting_subscription.getCausalityState() == "diverged":
    # Call it as soon as possible
    hosting_subscription.HostingSubscription_requestUpdateOpenSaleOrder()

  instance = hosting_subscription.getSuccessorValue()

  # This ensure that the user has a valid cloud contract.
  # At this stage he already have a paied invoice for the reservation,
  # so the cloud contact will be just created.
  instance.SoftwareInstance_requestValidationPayment()

  # create a Deduction for his fee
  context.SubscriptionRequest_generateReservationRefoundSalePackingList()

  # Instance is already destroyed so move into stopped state diretly.
  if hosting_subscription.getValidationState() == "archived":
    comment="Hosting Subscription is Destroyed and archived, Stop the Subscription Request"
    context.confirm(comment=comment)
    context.start(comment=comment)
    context.stop(comment=comment)

first_period_payment = context.SubscriptionRequest_verifyPaymentBalanceIsReady()
if not first_period_payment:
  # Payment isn't available for the user
  return "Skipped (Payment isn't ready)"

if not context.SubscriptionRequest_verifyInstanceIsAllocated():
  # Only continue if instance is ready
  return "Skipped (Instance isn't ready)"

invoice = first_period_payment.getCausalityValue()

# Link to be sent is the invoice one
if context.SubscriptionRequest_notifyPaymentIsReady(payment=invoice):
  context.confirm(comment="Payment is ready for the user")
  return "Payment is ready for the user"

return "Skipped (User isn't notified)"
