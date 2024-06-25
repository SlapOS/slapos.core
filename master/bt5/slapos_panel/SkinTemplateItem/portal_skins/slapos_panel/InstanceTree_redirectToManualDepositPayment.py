portal = context.getPortalObject()
web_site = context.getWebSiteValue()
assert web_site is not None

# This script will be used to generate the payment
# compatible with external providers
person = portal.portal_membership.getAuthenticatedMember().getUserValue()

# Fetch to know if the subscription request is already created
subscription_request = portal.portal_catalog.getResultValue(
  portal_type='Subscription Request',
  aggregate__uid=context.getUid())

if subscription_request is not None:
  if subscription_request.getSimulationState() != 'submitted':
    # No need to continue if the subscription is already processed.
    raise ValueError('No deposit is required, Subscription Request is not on submitted state')
else:
  subscription_request = context.Item_createSubscriptionRequest(temp_object=True)

if subscription_request is None:
  raise ValueError("Subscription Request was not found or generated")

outstanding_amount_list = person.Entity_getOutstandingDepositAmountList(
  ledger_uid=subscription_request.getLedgerUid(), 
  source_section_uid=subscription_request.getSourceSectionUid(),
  resource_uid=subscription_request.getPriceCurrencyUid())

if subscription_request.isTempObject():
  outstanding_amount_list.append(
    subscription_request.asContext(
      total_price=subscription_request.getPrice(None))
  )

payment_mode = subscription_request.Base_getPaymentModeForCurrency(
  subscription_request.getPriceCurrencyUid())

def wrapWithShadow(person, outstanding_amount_list, payment_mode):
  return person.Entity_createDepositPaymentTransaction(
    subscription_list=outstanding_amount_list,
    payment_mode=payment_mode
  )

# Use proper acquisiton to generate the payment transaction
person = web_site.restrictedTraverse(person.getRelativeUrl())

payment_transaction = person.Person_restrictMethodAsShadowUser(
  shadow_document=person,
  callable_object=wrapWithShadow,
  argument_list=[person, outstanding_amount_list, payment_mode])

return payment_transaction.PaymentTransaction_redirectToManualPayment()
