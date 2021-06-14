from DateTime import DateTime

state = context.getSimulationState()
transaction_amount = int(round((context.PaymentTransaction_getTotalPayablePrice() * -100), 2))
if (state != 'confirmed') or (context.getPaymentMode() != 'wechat') or (transaction_amount == 0):
  if (transaction_amount == 0):
    invoice = context.getCausalityValue(portal_types="Sale Invoice Transaction")
    if invoice is not None and round(invoice.getTotalPrice(), 2) == 0:
      context.edit(payment_mode="wire_transfer")
  return
else:
  # Request manual payment
  context.start(comment='Requested manual payment')
