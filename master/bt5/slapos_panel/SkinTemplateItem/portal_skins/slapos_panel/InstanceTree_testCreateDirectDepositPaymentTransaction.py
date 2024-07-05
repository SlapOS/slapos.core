from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

NOTHING_TO_PAY = context.Base_translateString('Nothing to pay')
NOTHING_TO_PAY_NO_PERSON = context.Base_translateString('Nothing to pay with your account')
PLEASE_CONTACT_US = context.Base_translateString('Please contact us to handle your payment')

portal = context.getPortalObject()
entity = portal.portal_membership.getAuthenticatedMember().getUserValue()
if entity is None:
  if return_message:
    return NOTHING_TO_PAY_NO_PERSON
  return False
# Fetch to know if the subscription request is already created
subscription_request = portal.portal_catalog.getResultValue(
  portal_type='Subscription Request',
  aggregate__uid=context.getUid())

price = 0
if subscription_request is None:
  subscription_request = context.Item_createSubscriptionRequest(temp_object=True)
  # Include temp object on the outstanting total price
  price = subscription_request.getPrice(None)
  if price is not None and price != 0:
    balance = entity.Entity_getDepositBalanceAmount([subscription_request])
    if balance > price:
      if return_message:
        return NOTHING_TO_PAY
      return False
elif subscription_request.getSimulationState() != 'submitted':
  # No need to continue if the subscription is already processed.
  if return_message:
    return NOTHING_TO_PAY
  return False

currency_uid = subscription_request.getPriceCurrencyUid()
if not return_message:
  # Return as early as possible if payment isnt configured
  if not context.Base_isExternalPaymentConfigured(currency_uid):
    return False

def getUidWithShadow(portal, source_section):
  # Source Section can be one organisation, so shadow is required
  # Shadow has no access to freshly created or temp subscription requests
  return portal.restrictedTraverse(source_section).getUid()

section_section_uid = entity.Person_restrictMethodAsShadowUser(
  shadow_document=entity, callable_object=getUidWithShadow,
  argument_list=[portal, subscription_request.getSourceSection()])

outstanding_amount_list = entity.Entity_getOutstandingDepositAmountList(
  ledger_uid=subscription_request.getLedgerUid(), 
  source_section_uid=section_section_uid,
  resource_uid=currency_uid)

assert len(outstanding_amount_list) in [0, 1]
outstanting_total_price = sum([i.total_price for i in outstanding_amount_list])
outstanting_total_price += price

if outstanting_total_price > 0:
  if return_message:
    assert not context.Base_isExternalPaymentConfigured(currency_uid), \
      "Payment is configured (and should not)"
    return PLEASE_CONTACT_US
  return True

if return_message:
  return NOTHING_TO_PAY
return False
