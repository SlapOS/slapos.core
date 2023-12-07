payment_mode = context.getPaymentMode()

entity = context.getDestinationSectionValue()

def wrapWithShadow(entity, invoice):
  return entity.Entity_createPaymentTransaction([invoice])

payment = entity.Person_restrictMethodAsShadowUser(
  shadow_document=entity,
  callable_object=wrapWithShadow,
  argument_list=[entity, context])

if web_site is None:
  web_site = context.getWebSiteValue() 

total_price = entity.Person_restrictMethodAsShadowUser(
  shadow_document=entity,
  callable_object=payment.PaymentTransaction_getTotalPayablePrice,
  argument_list=[])

if total_price >= 0:
  return payment.PaymentTransaction_redirectToManualFreePayment(web_site=web_site)

if payment_mode == "wechat":
  if payment.Base_getWechatServiceRelativeUrl():
    return payment.PaymentTransaction_redirectToManualWechatPayment(web_site=web_site)
elif payment_mode == "payzen":
  if payment.Base_getPayzenServiceRelativeUrl():
    return payment.PaymentTransaction_redirectToManualPayzenPayment(web_site=web_site)

return payment.PaymentTransaction_redirectToManualContactUsPayment(web_site=web_site)
