if not trade_no:
  raise Exception("You need to provide a trade number")

portal = context.getPortalObject()
payment = portal.accounting_module[trade_no]

if not payment:
  raise Exception("The payment with reference %s was not found" % trade_no)

payment.PaymentTransaction_updateWechatPaymentStatus()
return payment.getSimulationState()
