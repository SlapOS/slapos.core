payment = context.SubscriptionRequest_verifyPaymentBalanceIsReady()
if payment is not None and payment.getSimulationState() in ['stopped', 'deliveried']:
  # Payment Transaction is payed
  return True

# Payment Transaction ins't payed
return False
