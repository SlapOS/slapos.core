if context.getPaymentMode() == "payzen":
  reversal_payment = context.SaleInvoiceTransaction_createReversalPayzenTransaction()
elif context.getPaymentMode() == "wechat":
  reversal_payment = context.SaleInvoiceTransaction_createReversalWechatTransaction()
else:
  message = context.Base_translateString("The payment mode is unsupported.")
  return context.Base_redirect(keep_items={'portal_status_message': message})

message = context.Base_translateString("Reversal Transaction created.")
return reversal_payment.Base_redirect(keep_items={'portal_status_message': message})
