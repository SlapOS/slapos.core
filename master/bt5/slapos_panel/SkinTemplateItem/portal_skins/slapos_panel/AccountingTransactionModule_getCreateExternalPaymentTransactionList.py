from DateTime import DateTime
from zExceptions import Unauthorized
portal = context.getPortalObject()
entity = portal.portal_membership.getAuthenticatedMember().getUserValue()
if entity is None:
  raise Unauthorized

payment_dict_list = []

kw = {'ledger_uid' : portal.portal_categories.ledger.automated.getUid()}
for currency_uid, secure_service_relative_url in portal.Base_getSupportedExternalPaymentList():
  is_payment_configured = 1
  if secure_service_relative_url is None:
    is_payment_configured = 0

  kw['resource_uid'] = currency_uid
  for method in [entity.Entity_getOutstandingAmountList,
                 entity.Entity_getOutstandingDepositAmountList]:
    for outstanding_amount in method(**kw):
      if 0 < outstanding_amount.total_price:
        if not is_payment_configured:
          raise ValueError("Payment system is not properly configured")

        as_context_kw = {
          'total_price': outstanding_amount.total_price
        }
        if outstanding_amount.getPortalType() == "Subscription Request":
          as_context_kw['reference'] = "Subscriptions pre-payment"
          as_context_kw['stop_date'] = DateTime()

        payment_dict_list.append(
          outstanding_amount.asContext(**as_context_kw))

return payment_dict_list
