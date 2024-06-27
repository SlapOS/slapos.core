from zExceptions import Unauthorized
from DateTime import DateTime
if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()
web_site = context.getWebSiteValue()
assert web_site is not None

# This script will be used to generate the payment
# compatible with external providers

payment_dict_list = []

entity = portal.portal_membership.getAuthenticatedMember().getUserValue()
if entity is None:
  return '<p>Nothing to pay with your account</p>'

def isPaymentConfigured(currency_uid):
  for uid, secure_service_relative_url in [
      (portal.currency_module.EUR.getUid(), portal.Base_getPayzenServiceRelativeUrl()),
      # (portal.currency_module.CNY.getUid(), portal.Base_getWechatServiceRelativeUrl())
      ]:
    if currency_uid == uid and secure_service_relative_url is not None:
      return 1
  return 0

# Fetch to know if the subscription request is already created
subscription_request = portal.portal_catalog.getResultValue(
  portal_type='Subscription Request',
  aggregate__uid=context.getUid())

if subscription_request is not None:
  if subscription_request.getSimulationState() != 'submitted':
    # No need to continue if the subscription is already processed.
    return '<p>Nothing to pay</p>'
else:
  subscription_request = context.Item_createSubscriptionRequest(temp_object=True)

if subscription_request is not None:
  currency_uid = subscription_request.getPriceCurrencyUid()
  # Subscription is indexed so we just calculate like usual
  price = 0

  if subscription_request.isTempObject():
    # Include temp object on the outstanting total price
    price = subscription_request.getPrice(None)
    if price is not None and price != 0:
      balance = entity.Entity_getDepositBalanceAmount([subscription_request])
      if balance > price:
        return '<p>Nothing to Pay </p>'


  def getUidWithShadow(portal, source_section):
    # Source Section can be one organisation, so shadow is required
    # Shadow has no access to freshly created or temp subscription requests
    return (
      portal.restrictedTraverse(source_section).getUid(),
    )

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
    if not isPaymentConfigured(currency_uid):
      return '<p>Please contact us to handle your payment</p>'

    payment_url = subscription_request.absolute_url() + "/Base_createExternalPaymentTransactionFromOutstandingAmountAndRedirect" 
    if subscription_request.isTempObject():
      payment_url = context.absolute_url() + "/InstanceTree_redirectToManualDepositPayment"

    payment_dict_list.append({
      "reference": "Subscriptions pre-payment",
      # Format by hand is not a good idea probably
      "date": DateTime().strftime('%d/%m/%Y'),
      "url": payment_url,
      "total_price": outstanting_total_price,
      "currency": subscription_request.getPriceCurrencyReference()
    })

if not payment_dict_list:
  return '<p>Nothing to pay</p>'

# Pass argument via request.
context.REQUEST.set("payment_dict_list", payment_dict_list)
return context.Base_renderOutstandingAmountTable()
