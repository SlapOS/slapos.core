portal = context.getPortalObject()
Base_translateString = portal.Base_translateString
subscription_request = context

from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

batch = (dialog_id is None)
trade_condition_type = 'manual'

if activate_kw is None:
  activate_kw = {}
if not 'tag' in activate_kw:
  activate_kw['tag'] = script.id

if not (subscription_request.hasSourceSection() and (0 < subscription_request.getPrice(0))):
  keep_items = {
    'portal_status_level': 'warning',
    'portal_status_message': Base_translateString('The Subscription Request is not a payable one')
  }
  if batch:
    return subscription_request
  return context.Base_renderForm(dialog_id, keep_items=keep_items)

# Create the Subscription Change Request
item = subscription_request.getAggregateValue()
if item.getPortalType() == 'Project':
  project = item
else:
  project = subscription_request.getSourceProjectValue()

customer = subscription_request.getDestinationValue()
try:
  subscription_change_request = subscription_request.getResourceValue().Resource_createSubscriptionRequest(
    customer,
    # [software_type, software_release],
    subscription_request.getVariationCategoryList(),
    project,
    currency_value=subscription_request.getPriceCurrencyValue(),
    temp_object=True,
    item_value=item,
    causality_value=subscription_request,# XXX .getCausalityValue(),
    portal_type='Subscription Change Request',
    trade_condition_type=trade_condition_type
  )
except AssertionError:
  current_trade_condition = None
else:
  current_trade_condition = subscription_change_request.getSpecialiseValue()

new_sale_trade_condition = None
if (current_trade_condition is None):
  # Create a dedicated trade condition for the customer
  # to define free price
  previous_title = subscription_request.getTitle()
  specialise_trade_condition = subscription_request.getSpecialiseValue()
  while (specialise_trade_condition.hasSourceSection()) or (specialise_trade_condition.hasDestination()):
    previous_title = specialise_trade_condition.getTitle()
    specialise_trade_condition = specialise_trade_condition.getSpecialiseValue()

  new_sale_trade_condition = portal.sale_trade_condition_module.newContent(
    portal_type='Sale Trade Condition',
    specialise_value=specialise_trade_condition,
    title='%s for %s' % (previous_title, customer.getTitle()),
    destination_value=customer,
    destination_section_value=customer,
    source_project=subscription_request.getSourceProject(),
    source=subscription_request.getSource(),
    price_currency=subscription_request.getPriceCurrency(),
    trade_condition_type=trade_condition_type,
    activate_kw=activate_kw
  )
  new_sale_trade_condition.validate()
  subscription_request.activate(after_tag=activate_kw['tag']).SubscriptionRequest_changeFromPayableToFree(None)

  keep_items = {
    'portal_status_message': Base_translateString('Creating a free dedicated Trade Condition for the customer')
  }
  if batch:
    return new_sale_trade_condition
  return new_sale_trade_condition.Base_redirect(keep_items=keep_items)

elif (current_trade_condition.getDestination() == customer.getRelativeUrl()) and \
  (current_trade_condition.getSourceSection(None) is None):
  # There is already a manual trade condition
  # without any source section (free)
  new_sale_trade_condition = current_trade_condition

  subscription_change_request = subscription_request.getResourceValue().Resource_createSubscriptionRequest(
    customer,
    # [software_type, software_release],
    subscription_request.getVariationCategoryList(),
    project,
    currency_value=subscription_request.getPriceCurrencyValue(),
    item_value=item,
    causality_value=subscription_request,
    portal_type='Subscription Change Request',
    trade_condition_type=trade_condition_type
  )

  keep_items = {
    'portal_status_message': Base_translateString('Creating a Subscription Change Request')
  }
  if batch:
    return subscription_change_request
  return subscription_change_request.Base_redirect(keep_items=keep_items)

else:
  keep_items = {
    'portal_status_level': 'error',
    'portal_status_message': Base_translateString('This customer already has an incompatible dedicated Trade Condition')
  }
  if batch:
    raise ValueError(keep_items['portal_status_message'])
  return current_trade_condition.Base_redirect(keep_items=keep_items)
