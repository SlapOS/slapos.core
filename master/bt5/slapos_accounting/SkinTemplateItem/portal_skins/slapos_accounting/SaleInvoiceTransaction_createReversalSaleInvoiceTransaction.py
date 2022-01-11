""" Create a reversal transaction from current transaction. """
portal = context.getPortalObject()

if not batch_mode and context.getPaymentMode() not in ["payzen", "wechat"]:
  message = context.Base_translateString("The payment mode is unsupported.")
  return context.Base_redirect(keep_items={'portal_status_message': message})

# Check that we are in state that we are waiting for user manual payment
assert context.getPortalType() == 'Sale Invoice Transaction'
assert context.getPaymentMode() in ('payzen', 'wechat')
assert context.getSimulationState() == 'stopped'
assert context.getTotalPrice() != 0
assert context.getLedger() == 'automated'
assert context.getSpecialise(None) is not None

# Dont create if the invoice is already paied
assert not context.SaleInvoiceTransaction_isLettered()

payment = portal.portal_catalog.getResultValue(
  portal_type="Payment Transaction",
  simulation_state="started",
  default_causality_uid=context.getUid(),
  default_payment_mode_uid=[
    portal.portal_categories.payment_mode.payzen.getUid(),
    portal.portal_categories.payment_mode.wechat.getUid()],
)
if payment is not None:
  payment_mode = payment.getPaymentMode()
  if payment_mode == 'payzen' and payment.PaymentTransaction_getPayzenId()[1] is not None:
    # The payment transaction will be cancelled by a proper alarm.
    raise ValueError("Payment Transaction is waiting for External Payzen confirmation!")
  elif payment_mode == 'wechat' and payment.PaymentTransaction_getWechatId()[1] is not None:
    # The payment transaction will be cancelled by a proper alarm.
    raise ValueError("Payment Transaction is waiting for External Wechat confirmation!")

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

if batch_mode:
  return reversal_transaction

message = context.Base_translateString("Reversal Transaction created.")
return reversal_transaction.Base_redirect(
  keep_items={'portal_status_message': message})
