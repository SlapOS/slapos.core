from DateTime import DateTime
portal = context.getPortalObject()

state = context.getSimulationState()
if (state != 'started') or (context.getPaymentMode() != 'wechat'):
  return "state not started (%s)" % state
else:
  # ???
  transaction_date, transaction_id = context.PaymentTransaction_getWechatId()

  if transaction_id is not None:
    # so the payment is registered in wechat
    context.PaymentTransaction_createWechatEvent().updateStatus()
