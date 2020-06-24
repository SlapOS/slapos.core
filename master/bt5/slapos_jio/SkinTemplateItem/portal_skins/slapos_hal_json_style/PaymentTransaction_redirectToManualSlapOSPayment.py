payment_mode = context.getPaymentMode()

if payment_mode == "wechat":
  return context.PaymentTransaction_redirectToManualWechatPayment(web_site=web_site)
elif payment_mode == "payzen":
  return context.PaymentTransaction_redirectToManualPayzenPayment(web_site=web_site)

raise ValueError("%s isn't an acceptable payment mode" % payment_mode)
