portal = context.getPortalObject()

currency_value = None
if currency_reference:
  currency_value = portal.portal_catalog.getResultValue(
    portal_type="Currency",
    reference=currency_reference,
    validation_state=("validated", "published"))

if currency_value is None:
  raise ValueError("Unknown Currency: %s" % currency_reference)

ledger_uid = portal.portal_categories.ledger.automated.getUid()
currency_uid = currency_value.getUid()

payment_mode = context.Base_getPaymentModeForCurrency(currency_value.getUid())

outstanding_amount_list = context.Entity_getOutstandingDepositAmountList(
  resource_uid=currency_uid, ledger_uid=ledger_uid)

if len(outstanding_amount_list) != 1:
  raise ValueError("It was expected exactly one amount to pay for %s currency (%s found)" % (
    currency_uid, outstanding_amount_list))

deposit_price = outstanding_amount_list[0].total_price
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
return payment_transaction.PaymentTransaction_redirectToManualPayment(web_site=web_site)
