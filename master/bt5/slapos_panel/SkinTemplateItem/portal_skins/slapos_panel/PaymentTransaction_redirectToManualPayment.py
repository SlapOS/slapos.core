if (context.getPaymentMode() == "wechat"):
  return context.PaymentTransaction_redirectToManualWechatPayment()
elif (context.getPaymentMode() == "payzen"):
  return context.PaymentTransaction_redirectToManualPayzenPayment()
else:
  return context.PaymentTransaction_triggerPaymentCheckAlarmAndRedirectToPanel(result="contact_us")
