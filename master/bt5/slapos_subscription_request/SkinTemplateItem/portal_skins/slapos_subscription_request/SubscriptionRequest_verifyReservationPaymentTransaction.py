from DateTime import DateTime

if context.getSimulationState() != "draft":
  return

sale_invoice_transaction = context.getCausalityValue(
  portal_type="Sale Invoice Transaction")

if sale_invoice_transaction is None:
  if context.getCreationDate() < DateTime() - 1:
    context.cancel(comment="No sale invoice transaction attached, so subscription is cancelled")
  return

if sale_invoice_transaction.getSimulationState() in ["draft", "cancelled", "deleted"]:
  context.cancel(comment="Invoice is cancelled, so subscription is cancelled")
  return

payment_transaction_list = sale_invoice_transaction.getCausalityRelatedValueList(
  portal_type="Payment Transaction")

cancel_subscription_request = None
is_paid = False
for payment_transaction in payment_transaction_list:
  if cancel_subscription_request != False and payment_transaction.getSimulationState() in ["draft", "cancelled", "deleted"]:
    cancel_subscription_request = True
  
  if payment_transaction.getSimulationState() == "stopped":
    cancel_subscription_request = False
    is_paid = True

if cancel_subscription_request:
  context.cancel(comment="Payment is cancelled, so subscription is cancelled")
  sale_invoice_transaction.cancel(comment="Payment is cancelled, so invoice is cancelled")
  for payment_transaction in payment_transaction_list:
    if payment_transaction.getSimulationState() == "started":
      payment_transaction.cancel("Subscription is been cancelled")


# Check if payment_transaction is payed.
if not is_paid:
  # Nothing to do bug wait the payment
  return

if context.getSpecialise(portal_type="Subscription Condition") is not None:
  # Ensure Subscription is updated
  context.SubscriptionRequest_applyCondition()

context.plan(comment="Payment is consider valid.")
