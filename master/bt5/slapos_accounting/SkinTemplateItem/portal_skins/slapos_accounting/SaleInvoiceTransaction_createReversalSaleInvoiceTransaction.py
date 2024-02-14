""" Create a reversal transaction from current transaction. """
from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()

# Check that we are in state that we are waiting for user manual payment
assert context.getPortalType() == 'Sale Invoice Transaction'
assert context.getSimulationState() in ('stopped', 'delivered')
assert context.getTotalPrice() != 0

# Dont create if the invoice is already paid
assert not context.SaleInvoiceTransaction_isLettered()

payment = portal.portal_catalog.getResultValue(
  portal_type="Payment Transaction",
  simulation_state="started",
  default_causality_uid=context.getUid()
)
if payment is not None:
  raise ValueError("Payment Transaction is waiting for confirmation!")

# Should be safe now to fix everything
reversal_transaction = context.Base_createCloneDocument(batch_mode=1)

reversal_transaction.edit(
  title="Reversal Transaction for %s" % context.getTitle(),
  causality_value=context,
  description="Reversal Transaction for %s" % context.getTitle(),
  specialise_value=portal.sale_trade_condition_module.slapos_manual_accounting_trade_condition,
)

for line in reversal_transaction.getMovementList():
  line.edit(quantity=(-line.getQuantity()))

reversal_transaction.confirm(comment="Automatic because of reversal creation")
reversal_transaction.stop(comment="Automatic because of reversal creation")

if batch_mode:
  return reversal_transaction

message = context.Base_translateString("Reversal Transaction created.")
return reversal_transaction.Base_redirect(
  keep_items={'portal_status_message': message})
