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

instance_tree = context.getAggregateValue(portal_type="Instance Tree")
instance_tree_state = "Instance Tree Not Found"

if instance_tree is not None:
  unallocated_instance_list = len([
    x for x in instance_tree.getSpecialiseRelatedValueList(portal_type=["Software Instance", "Slave Instance"]) 
      if x.getAggregateValue() is None])

  if  unallocated_instance_list > 0:
    instance_tree_state = "Allocation Unfinished"
  else:
    instance_tree_state = "OK"

return """
Title: %s
State: %s
Reservation Fee State: %s
Instance Tree State: %s
""" % (context.getTitle(),
      context.getSimulationStateTitle(),
      reservation_fee_state,
      instance_tree_state)
