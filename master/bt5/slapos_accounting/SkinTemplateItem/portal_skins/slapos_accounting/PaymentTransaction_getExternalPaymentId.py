from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

payment_mode = context.getPaymentMode()
if payment_mode == "payzen":
  return context.PaymentTransaction_getPayzenId()
elif payment_mode == "wechat":
  return context.PaymentTransaction_getWechatId()

raise ValueError("Unsupported External Payment Mode, please use Payzen or Wechat")
