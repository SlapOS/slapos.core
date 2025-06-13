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

payment_mode = subscription_request.Base_getPaymentModeForCurrency(
  subscription_request.getPriceCurrencyUid())

temp_subscription_dict = None
if subscription_request.isTempObject():
  # Populate the dict to recreate the temp object under SHADOW user
  # Otherwise security will raise late own, because SHADOW has no access to
  # draft subscription request because it is not the owner of it.
  # Change state or updateLocalRolesOnSecurityGroups were tried, also create
  # the object under shadow. Despite been verbose, it is the simplest way to
  # workaround the problem.
  temp_subscription_dict = {
    'destination': subscription_request.getDestination(),
    'destination_section': subscription_request.getDestinationSection(),
    'destination_decision': subscription_request.getDestinationDecision(),
    'destination_project': subscription_request.getDestinationProject(),
    'start_date': subscription_request.getStartDate(),
    'effective_date': subscription_request.getEffectiveDate(),
    'resource': subscription_request.getResource(),
    'variation_category_list': subscription_request.getVariationCategoryList(),
    'aggregate': subscription_request.getAggregate(),
    'quantity_unit': subscription_request.getQuantityUnit(),
    'quantity': subscription_request.getQuantity(),
    'ledger': subscription_request.getLedger(),
    'specialise': subscription_request.getSpecialise(),
    'source': subscription_request.getSource(),
    'source_section': subscription_request.getSourceSection(),
    'source_project': subscription_request.getSourceProject(),
    'price_currency': subscription_request.getPriceCurrency(),
    'price': subscription_request.getPrice(None),
    'causality': subscription_request.getCausality()
  }


def wrapWithShadowToNotGetUnauthorized(person, ledger_uid,
                                       section, resource_uid,
                                       payment_mode,
                                       temp_subscription_dict):

  # Required because user cannot access organisation module
  section_uid = portal.restrictedTraverse(section).getUid()
  outstanding_amount_list = person.Entity_getOutstandingDepositAmountList(
    ledger_uid=ledger_uid,
    section_uid=section_uid,
    resource_uid=resource_uid)

  if temp_subscription_dict is not None:
    temp_subscription_request = portal.portal_trash.newContent(
      portal_type="Subscription Request",
      temp_object=True,
      **temp_subscription_dict)
    outstanding_amount_list.append(temp_subscription_request.asContext(
      total_price=temp_subscription_request.getPrice(None)))

  return person.Entity_createDepositPaymentTransaction(
    subscription_list=outstanding_amount_list,
    payment_mode=payment_mode
  )

payment_transaction = person.Person_restrictMethodAsShadowUser(
  shadow_document=person,
  callable_object=wrapWithShadowToNotGetUnauthorized,
  argument_list=[person,
    subscription_request.getLedgerUid(),
    subscription_request.getSourceSection(),
    subscription_request.getPriceCurrencyUid(),
    payment_mode,
    temp_subscription_dict])

return payment_transaction.PaymentTransaction_redirectToManualPayment()
