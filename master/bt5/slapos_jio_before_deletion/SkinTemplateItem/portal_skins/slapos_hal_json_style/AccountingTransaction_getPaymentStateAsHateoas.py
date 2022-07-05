state = context.AccountingTransaction_getPaymentState()
payment_mode = None
if state == "Pay Now":
  payment_mode = context.getPaymentMode() # ???

return {"state": context.Base_translateString(state),
        "payment_mode": payment_mode}
