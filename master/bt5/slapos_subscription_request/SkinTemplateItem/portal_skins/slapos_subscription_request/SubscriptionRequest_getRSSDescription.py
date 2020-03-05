reservation_fee_state = "Invoice Not Found"

sale_invoice_transaction = context.getCausalityValue(
  portal_type="Sale Invoice Transaction")

if sale_invoice_transaction is not None:
  payment_transaction = sale_invoice_transaction.getCausalityRelatedValue(
    portal_type="Payment Transaction")
  if payment_transaction is not None:
    # Check if payment_transaction is payed.
    if payment_transaction.getSimulationState() != "stopped":
      # Nothing to do bug wait the payment
      reservation_fee_state = "Unpaid"
    else:
      reservation_fee_state = "Paid"

hosting_subscription = context.getAggregateValue(portal_type="Hosting Subscription")
hosting_subscription_state = "Hosting Subscription Not Found"

if hosting_subscription is not None:
  unallocated_instance_list = len([
    x for x in hosting_subscription.getSpecialiseRelatedValueList(portal_type=["Software Instance", "Slave Instance"]) 
      if x.getAggregateValue() is None])

  if  unallocated_instance_list > 0:
    hosting_subscription_state = "Allocation Unfinished"
  else:
    hosting_subscription_state = "OK"

return """
Title: %s
State: %s
Reservation Fee State: %s
Hosting Subscription State: %s
""" % (context.getTitle(),
      context.getSimulationStateTitle(),
      reservation_fee_state,
      hosting_subscription_state)
