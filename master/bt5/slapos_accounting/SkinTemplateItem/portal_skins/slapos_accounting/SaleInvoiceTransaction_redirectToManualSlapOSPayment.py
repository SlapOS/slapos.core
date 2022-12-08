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

if payment_mode == "wechat":
  return payment.PaymentTransaction_redirectToManualWechatPayment(web_site=web_site)
elif payment_mode == "payzen":
  return payment.PaymentTransaction_redirectToManualPayzenPayment(web_site=web_site)

raise ValueError("%s isn't an acceptable payment mode" % payment_mode)
