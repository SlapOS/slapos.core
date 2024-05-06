from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()
ledger_uid = portal.portal_categories.ledger.automated.getUid()

if currency_uid is None:
  currency_uid = context.getPriceCurrency()


deposit_price = 0
for sql_subscription_request in portal.portal_catalog(
  portal_type="Subscription Request",
  simulation_state='submitted',
  destination_section__uid=context.getUid(),
  price_currency__uid=currency_uid,
  ledger__uid=ledger_uid
):
  subscription_request = sql_subscription_request.getObject()
  subscription_request_total_price = subscription_request.getTotalPrice()
  if 0 < subscription_request_total_price:
    deposit_price += subscription_request_total_price

return deposit_price
