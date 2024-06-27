from zExceptions import Unauthorized
from DateTime import DateTime
if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()
web_site = context.getWebSiteValue()
assert web_site is not None

ledger_uid = portal.portal_categories.ledger.automated.getUid()

# This script will be used to generate the payment
# compatible with external providers
entity = portal.portal_membership.getAuthenticatedMember().getUserValue()
if entity is None:
  return '<p>Nothing to pay with your account</p>'

payment_dict_list = []

for currency_uid, secure_service_relative_url in [
  (portal.currency_module.EUR.getUid(), portal.Base_getPayzenServiceRelativeUrl()),
  # (portal.currency_module.CNY.getUid(), portal.Base_getWechatServiceRelativeUrl())
]:
  is_payment_configured = 1
  if secure_service_relative_url is None:
    is_payment_configured = 0

  for method in [entity.Entity_getOutstandingAmountList,
                  entity.Entity_getOutstandingDepositAmountList]:
    for outstanding_amount in method(
         ledger_uid=ledger_uid, resource_uid=currency_uid):
      if 0 < outstanding_amount.total_price:
        if not is_payment_configured:
          return '<p>Please contact us to handle your payment</p>'

        reference = outstanding_amount.getReference()
        stop_date = outstanding_amount.getStopDate()
        if outstanding_amount.getPortalType() == "Subscription Request":
          reference = "Subscriptions pre-payment"
          stop_date = DateTime()
        payment_dict_list.append({
          "reference": reference,
          # Format by hand is not a good idea probably
          "date": stop_date.strftime('%d/%m/%Y'),
          "url": '%s/Base_createExternalPaymentTransactionFromOutstandingAmountAndRedirect' % outstanding_amount.absolute_url(),
          "total_price": outstanding_amount.total_price,
          "currency": outstanding_amount.getPriceCurrencyReference()
        })

if not payment_dict_list:
  return '<p>Nothing to pay</p>'

# Pass argument via request.
context.REQUEST.set("payment_dict_list", payment_dict_list)
return context.Base_renderOutstandingAmountTable()
