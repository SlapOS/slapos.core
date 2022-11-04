state = context.AccountingTransaction_getPaymentState()
payment_transaction = None
payment_mode = None
if state == "Pay now":
  payment_transaction_value = context.SaleInvoiceTransaction_getSlapOSPaymentRelatedValue()
  payment_transaction = payment_transaction_value.getRelativeUrl()
  payment_mode = payment_transaction_value.getPaymentMode()

return {"state": context.Base_translateString(state),
        "payment_mode": payment_mode,
        "payment_transaction": payment_transaction}
