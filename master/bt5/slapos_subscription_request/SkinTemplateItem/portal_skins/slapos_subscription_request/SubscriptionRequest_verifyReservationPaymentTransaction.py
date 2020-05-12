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

payment_transaction = sale_invoice_transaction.getCausalityRelatedValue(
  portal_type="Payment Transaction")

if payment_transaction.getSimulationState() in ["draft", "cancelled", "deleted"]:
  context.cancel(comment="Payment is cancelled, so subscription is cancelled")
  sale_invoice_transaction.cancel(comment="Payment is cancelled, so invoice is cancelled")
  return

# Check if payment_transaction is payed.
if payment_transaction.getSimulationState() != "stopped":
  # Nothing to do bug wait the payment
  return

if context.getSpecialise(portal_type="Subscription Condition") is not None:
  # Ensure Subscription is updated
  context.SubscriptionRequest_applyCondition()

context.plan(comment="Payment is consider valid.")
