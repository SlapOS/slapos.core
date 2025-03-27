portal = context.getPortalObject()
web_site = context.getWebSiteValue()
assert web_site is not None

# This script will be used to generate the payment
# compatible with external providers
person = portal.portal_membership.getAuthenticatedMember().getUserValue()

# Use proper acquisiton to generate the payment transaction
person = web_site.restrictedTraverse(person.getRelativeUrl())

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

initial_outstanting_list = []

if subscription_request.isTempObject():
  initial_outstanting_list.append(
    subscription_request.asContext(
      total_price=subscription_request.getPrice(None))
  )

payment_mode = subscription_request.Base_getPaymentModeForCurrency(
  subscription_request.getPriceCurrencyUid())

def wrapWithShadowToNotGetUnauthorized(person, ledger_uid,
                                       section, resource_uid,
                                       payment_mode,
                                       initial_outstanting_list):

  # Required because user cannot access organisation module
  section_uid = portal.restrictedTraverse(section).getUid()
  outstanding_amount_list = person.Entity_getOutstandingDepositAmountList(
    ledger_uid=ledger_uid,
    section_uid=section_uid,
    resource_uid=resource_uid)

  outstanding_amount_list.extend(initial_outstanting_list)
  return person.Entity_createDepositPaymentTransaction(
    subscription_list=outstanding_amount_list,
    payment_mode=payment_mode
  )

payment_transaction = person.Person_restrictMethodAsShadowUser(
  shadow_document=person,
  callable_object=wrapWithShadowToNotGetUnauthorized,
  argument_list=[person, subscription_request.getLedgerUid(),
    subscription_request.getSourceSection(),
    subscription_request.getPriceCurrencyUid(),
    payment_mode,
    initial_outstanting_list])

return payment_transaction.PaymentTransaction_redirectToManualPayment()
