""" Create a reversal transaction from current payzen transaction. """
from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()

# Check that we are in state that we are waiting for user manual payment
assert context.getPortalType() == 'Sale Invoice Transaction'
assert context.getPaymentMode() == 'payzen'
assert context.getSimulationState() == 'stopped'
assert context.getTotalPrice() != 0
assert context.getSpecialise() in ("sale_trade_condition_module/slapos_aggregated_trade_condition",
                                   "sale_trade_condition_module/slapos_aggregated_subscription_trade_condition")


# Dont create if the invoice is already paied
assert not context.SaleInvoiceTransaction_isLettered()

payment = portal.portal_catalog.getResultValue(
  portal_type="Payment Transaction",
  simulation_state="started",
  default_causality_uid=context.getUid(),
  default_payment_mode_uid=portal.portal_categories.payment_mode.payzen.getUid(),
)
if payment is not None and payment.PaymentTransaction_getPayzenId()[1] is None:
  # The payment transaction will be cancelled by a proper alarm.
  raise ValueError("Payment Transaction is waiting for External Payzen confirmation!")

# Should be safe now to fix everything
context.SaleInvoiceTransaction_resetPaymentMode()
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

return reversal_transaction
