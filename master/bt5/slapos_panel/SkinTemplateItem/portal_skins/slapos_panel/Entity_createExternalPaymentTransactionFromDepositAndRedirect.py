portal = context.getPortalObject()
entity = portal.portal_membership.getAuthenticatedMember().getUserValue()

web_site = context.getWebSiteValue()
ledger_uid = portal.portal_categories.ledger.automated.getUid()
currency_uid = portal.currency_module.EUR.getUid()

if currency_uid == None:
  currency_uid = portal.currency_module.EUR.getUid()

assert web_site is not None
assert web_site.getLayoutProperty("configuration_payment_url_template", None) is not None
assert entity.getUid() == context.getUid()

deposit_price = 0
for sql_subscription_request in portal.portal_catalog(
  portal_type="Subscription Request",
  simulation_state='submitted',
  destination_section__uid=entity.getUid(),
  price_currency__uid=currency_uid,
  ledger__uid=ledger_uid
):
  subscription_request = sql_subscription_request.getObject()
  subscription_request_total_price = subscription_request.getTotalPrice()
  if 0 < subscription_request_total_price:
    deposit_price += subscription_request_total_price

if 0 >= deposit_price:
  raise ValueError("Nothing to pay")

payment_mode = None
resource_uid = currency_uid
for accepted_resource_uid, accepted_payment_mode, is_activated in [
  (portal.currency_module.EUR.getUid(), 'payzen', portal.Base_getPayzenServiceRelativeUrl()),
]:
  if is_activated and (resource_uid == accepted_resource_uid):
    payment_mode = accepted_payment_mode

assert payment_mode is not None

def wrapWithShadow(entity, total_amount, currency_uid):
  currency_value = portal.portal_catalog.getObject(uid=currency_uid)
  if currency_value is None:
    raise ValueError("Currency not found")
  return entity.Person_addDepositPayment(
    total_amount,
    currency_value.getRelativeUrl(),
    batch=1
  )

payment_transaction = entity.Person_restrictMethodAsShadowUser(
  shadow_document=entity,
  callable_object=wrapWithShadow,
  argument_list=[entity, deposit_price, currency_uid])

web_site = context.getWebSiteValue()

if (payment_mode == "wechat"):
  return payment_transaction.PaymentTransaction_redirectToManualWechatPayment(web_site=web_site)
elif (payment_mode == "payzen"):
  return payment_transaction.PaymentTransaction_redirectToManualPayzenPayment(web_site=web_site)
else:
  raise NotImplementedError('not implemented')
