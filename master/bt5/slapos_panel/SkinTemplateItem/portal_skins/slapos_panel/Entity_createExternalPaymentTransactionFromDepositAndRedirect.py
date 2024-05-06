portal = context.getPortalObject()

web_site = context.getWebSiteValue()

if currency_reference is not None:
  currency_value = portal.portal_catalog.getResultValue(
    portal_type="Currency",
    reference=currency_reference,
    validation_state="validated")
  
if currency_value is None:
  raise ValueError("Unknown Currency: %s" % currency_reference)

currency_uid = currency_value.getUid()

assert web_site is not None

deposit_price = context.Entity_getOutstandingDepositAmount(currency_uid)
if 0 >= deposit_price:
  raise ValueError("Nothing to pay")

payment_mode = None
resource_uid = currency_uid
for accepted_resource_uid, accepted_payment_mode, is_activated in [
  (portal.currency_module.EUR.getUid(), 'payzen', portal.Base_getPayzenServiceRelativeUrl()),
  # (portal.currency_module.CNY, 'wechat', portal.Base_getWechatServiceRelativeUrl())

]:
  if is_activated and (resource_uid == accepted_resource_uid):
    payment_mode = accepted_payment_mode

assert payment_mode is not None

def wrapWithShadow(entity, total_amount, currency_value):
  return entity.Person_addDepositPayment(
    total_amount,
    currency_value.getRelativeUrl(),
    batch=1
  )

payment_transaction = context.Person_restrictMethodAsShadowUser(
  shadow_document=context,
  callable_object=wrapWithShadow,
  argument_list=[context, deposit_price, currency_value])
 
if (payment_mode == "wechat"):
  return payment_transaction.PaymentTransaction_redirectToManualWechatPayment(web_site=web_site)
elif (payment_mode == "payzen"):
  return payment_transaction.PaymentTransaction_redirectToManualPayzenPayment(web_site=web_site)
else:
  raise NotImplementedError('not implemented')
