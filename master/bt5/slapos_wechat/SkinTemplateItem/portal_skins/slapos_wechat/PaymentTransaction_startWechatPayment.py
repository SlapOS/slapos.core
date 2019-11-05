from DateTime import DateTime

state = context.getSimulationState()
transaction_amount = int(round((context.PaymentTransaction_getTotalPayablePrice() * -100), 2))
if (state != 'confirmed') or (context.getPaymentMode() != 'wechat') or (transaction_amount == 0):
  return
else:
  # Request manual payment
  context.start(comment='Requested manual payment')
