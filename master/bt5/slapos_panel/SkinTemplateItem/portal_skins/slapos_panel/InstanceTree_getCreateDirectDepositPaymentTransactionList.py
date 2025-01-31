from zExceptions import Unauthorized
from DateTime import DateTime

portal = context.getPortalObject()
entity = portal.portal_membership.getAuthenticatedMember().getUserValue()
if entity is None:
  return Unauthorized

# Fetch to know if the subscription request is already created
subscription_request = portal.portal_catalog.getResultValue(
  portal_type='Subscription Request',
  aggregate__uid=context.getUid())

price = 0
payment_list = []

if subscription_request is None:
  subscription_request = context.Item_createSubscriptionRequest(temp_object=True)
  # Include temp object on the outstanting total price
  price = subscription_request.getPrice(None)
  if price is not None and price != 0:
    balance = entity.Entity_getDepositBalanceAmount([subscription_request])
    if balance > price:
      return payment_list
elif subscription_request.getSimulationState() != 'submitted':
  # No need to continue if the subscription is already processed.
  return payment_list

def getUidWithShadow(portal, source_section):
  # Source Section can be one organisation, so shadow is required
  # Shadow has no access to freshly created or temp subscription requests
  return portal.restrictedTraverse(source_section).getUid()

currency_uid = subscription_request.getPriceCurrencyUid()
section_section_uid = entity.Person_restrictMethodAsShadowUser(
  shadow_document=entity,
  callable_object=getUidWithShadow,
  argument_list=[portal, subscription_request.getSourceSection()])

outstanding_amount_list = entity.Entity_getOutstandingDepositAmountList(
  ledger_uid=subscription_request.getLedgerUid(),
  source_section_uid=section_section_uid,
  resource_uid=currency_uid)

assert len(outstanding_amount_list) in [0, 1]
outstanting_total_price = sum([i.total_price for i in outstanding_amount_list])
outstanting_total_price += price

if outstanting_total_price > 0:
  if not context.Base_isExternalPaymentConfigured(currency_uid):
    raise ValueError("External Payment support is not configured")

  if len(outstanding_amount_list) == 0:
    # return payment_list
    payment_list.append(context.asContext(
      reference="Subscriptions pre-payment",
      # Format by hand is not a good idea probably
      stop_date=DateTime().strftime('%d/%m/%Y'),
      resource_uid=currency_uid,
      total_price=price,
    ))
  else:
    payment_list.append(outstanding_amount_list[0].asContext(
      reference="Subscriptions pre-payment",
      # Format by hand is not a good idea probably
      stop_date=DateTime().strftime('%d/%m/%Y'),
      total_price=outstanting_total_price,
    ))

return payment_list
