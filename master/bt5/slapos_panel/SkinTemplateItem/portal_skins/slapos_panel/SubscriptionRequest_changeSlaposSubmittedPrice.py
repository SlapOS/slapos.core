from DateTime import DateTime

portal = context.getPortalObject()
Base_translateString = portal.Base_translateString
subscription_request = context

from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

batch = (dialog_id is None)
if activate_kw is None:
  activate_kw = {}
tag = activate_kw.get('tag', script.id)
activate_kw['tag'] = tag

######################################################
# Prevent some mistakes
if subscription_request.getSimulationState() != 'submitted':
  keep_items = {
    'portal_status_level': 'warning',
    'portal_status_message': Base_translateString('Can only change submitted subscription request')
  }
  if batch:
    raise ValueError(keep_items['portal_status_message'])
  return subscription_request.Base_redirect(keep_items=keep_items)

current_price = subscription_request.getPrice()
if not current_price:
  keep_items = {
    'portal_status_level': 'warning',
    'portal_status_message': Base_translateString('Can not make a free subscription to a payable one')
  }
  if batch:
    raise ValueError(keep_items['portal_status_message'])
  return subscription_request.Base_redirect(keep_items=keep_items)

######################################################
# From payable to free
if not price:
  return subscription_request.SubscriptionRequest_changeFromPayableToFree(dialog_id)

######################################################
# Change price
portal_type = 'Subscription Change Request'
subscription_change_request = portal.getDefaultModule(portal_type).newContent(
  portal_type=portal_type,
  causality_value=subscription_request,
  start_date=DateTime(),
  price=price,
  # Copy all other properties
  destination=subscription_request.getDestination(),
  destination_section=subscription_request.getDestinationSection(),
  destination_decision=subscription_request.getDestinationDecision(),
  destination_project=subscription_request.getDestinationProject(),
  resource=subscription_request.getResource(),
  aggregate=subscription_request.getAggregate(),
  variation_category_list=subscription_request.getVariationCategoryList(),
  quantity_unit=subscription_request.getQuantityUnit(),
  quantity=subscription_request.getQuantity(),
  ledger=subscription_request.getLedger(),
  source=subscription_request.getSource(),
  source_section=subscription_request.getSourceSection(),
  source_project=subscription_request.getSourceProject(),
  price_currency=subscription_request.getPriceCurrency(),
  specialise=subscription_request.getSpecialise(),
)
subscription_change_request.submit()

keep_items = {
  'portal_status_message': Base_translateString('Subscription Change Request created')
}
if batch:
  return subscription_change_request
return subscription_change_request.Base_redirect(keep_items=keep_items)
