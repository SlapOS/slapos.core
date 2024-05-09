portal = context.getPortalObject()

currency_value = None
if currency_reference:
  currency_value = portal.portal_catalog.getResultValue(
    portal_type="Currency",
    reference=currency_reference,
    validation_state="validated")

if currency_value is None:
  raise ValueError("Unknown Currency: %s" % currency_reference)

deposit_price = context.Entity_getOutstandingDepositAmount(currency_value.getUid())
if 0 >= deposit_price:
  raise ValueError("Nothing to pay")

def wrapWithShadow(entity, total_amount, currency_value):
  return entity.Person_addDepositPayment(
    total_amount,
    currency_value.getRelativeUrl(),
  )

payment_transaction = context.Person_restrictMethodAsShadowUser(
  shadow_document=context,
  callable_object=wrapWithShadow,
  argument_list=[context, deposit_price, currency_value])

web_site = context.getWebSiteValue()
assert web_site is not None
return payment_transaction.PaymentTransaction_redirectToManualPayment(web_site=web_site)
