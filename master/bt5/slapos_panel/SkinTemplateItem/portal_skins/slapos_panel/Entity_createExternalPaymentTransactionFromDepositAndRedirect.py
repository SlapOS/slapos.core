portal = context.getPortalObject()

currency_value = None
if currency_reference:
  currency_value = portal.portal_catalog.getResultValue(
    portal_type="Currency",
    reference=currency_reference,
    validation_state=("validated", "published"))

if currency_value is None:
  raise ValueError("Unknown Currency: %s" % currency_reference)

payment_mode = context.Base_getPaymentModeForCurrency(currency_value.getUid())
assert payment_mode is not None

deposit_price = context.Entity_getOutstandingDepositAmount(currency_value.getUid())
if 0 >= deposit_price:
  raise ValueError("Nothing to pay")

def wrapWithShadow(entity, total_amount, currency_value, payment_mode):
  return entity.Entity_addDepositPayment(
    total_amount,
    currency_value.getRelativeUrl(),
    payment_mode=payment_mode
  )

payment_transaction = context.Person_restrictMethodAsShadowUser(
  shadow_document=context,
  callable_object=wrapWithShadow,
  argument_list=[context, deposit_price, currency_value, payment_mode])

web_site = context.getWebSiteValue()
assert web_site is not None
return payment_transaction.PaymentTransaction_redirectToManualPayment(web_site=web_site)
