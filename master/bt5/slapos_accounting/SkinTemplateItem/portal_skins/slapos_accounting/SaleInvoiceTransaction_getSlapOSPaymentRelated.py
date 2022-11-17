payment_transaction = context.SaleInvoiceTransaction_getSlapOSPaymentRelatedValue()
if payment_transaction is not None:
  return payment_transaction.getRelativeUrl()
