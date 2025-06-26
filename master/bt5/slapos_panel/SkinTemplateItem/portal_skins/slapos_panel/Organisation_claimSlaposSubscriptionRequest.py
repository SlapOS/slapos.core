portal = context.getPortalObject()
Base_translateString = portal.Base_translateString
organisation = context

from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

batch = (dialog_id is None)
if activate_kw is None:
  activate_kw = {}
tag = activate_kw.get('tag', script.id)
activate_kw['tag'] = tag

# Search for the matching item
sql_subscription_request_list = portal.portal_catalog(
  reference=reference,
  # Project are not handled yet, as it must also move all compute node subscription at the same time
  portal_type=['Subscription Request'],
  simulation_state='submitted',
  limit=2
)
if len(sql_subscription_request_list) != 1:
  keep_items = {
    'your_reference': reference,
    'portal_status_level': 'warning',
    'portal_status_message': Base_translateString('Unknown reference')
  }
  if batch:
    raise ValueError(keep_items['portal_status_message'] + str(len(sql_subscription_request_list)))
  return context.Base_renderForm(dialog_id, keep_items=keep_items)

subscription_request = sql_subscription_request_list[0].getObject()

if subscription_request.getDestinationSection() == organisation.getRelativeUrl():
  keep_items = {
    'your_reference': reference,
    'portal_status_level': 'warning',
    'portal_status_message': Base_translateString('The Subscription Request is already paid by this organisation')
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

subscription_change_request = subscription_request.getResourceValue().Resource_createSubscriptionRequest(
  subscription_request.getDestinationValue(),
  # [software_type, software_release],
  subscription_request.getVariationCategoryList(),
  project,
  currency_value=subscription_request.getPriceCurrencyValue(),
  item_value=item,
  causality_value=subscription_request.getCausalityValue(),
  temp_object=True,
  portal_type='Subscription Change Request'
)
current_trade_condition = subscription_change_request.getSpecialiseValue()

if (current_trade_condition.getDestination() is None):
  # Create a dedicated trade condition for the customer
  # to define the payment by this organisation
  customer = subscription_request.getDestinationValue()
  new_sale_trade_condition = portal.sale_trade_condition_module.newContent(
    portal_type='Sale Trade Condition',
    specialise_value=current_trade_condition,
    title='%s for %s' % (current_trade_condition.getTitle(), customer.getTitle()),
    destination_value=customer,
    destination_section_value=organisation,
    source_project=current_trade_condition.getSourceProject(),
    price_currency=current_trade_condition.getPriceCurrency(),
    trade_condition_type=current_trade_condition.getTradeConditionType(),
    effective_date=current_trade_condition.getEffectiveDate(),
    activate_kw=activate_kw
  )
  new_sale_trade_condition.validate()
  context.activate(activity='SQLQueue', after_tag=tag).Organisation_claimSlaposSubscriptionRequest(reference, None, activate_kw)
  keep_items = {
    'portal_status_message': Base_translateString('Creating a dedicated Trade Condition for the customer')
  }
  if batch:
    return new_sale_trade_condition
  return new_sale_trade_condition.Base_redirect(keep_items=keep_items)

else:
  subscription_change_request = subscription_request.getResourceValue().Resource_createSubscriptionRequest(
    subscription_request.getDestinationValue(),
    # [software_type, software_release],
    subscription_request.getVariationCategoryList(),
    project,
    currency_value=subscription_request.getPriceCurrencyValue(),
    item_value=item,
    causality_value=subscription_request,
    portal_type='Subscription Change Request'
  )
  keep_items = {
    'your_reference': reference,
    'portal_status_level': 'error',
    'portal_status_message': Base_translateString('This customer already has a dedicated Trade Condition')
  }
  if batch:
    return subscription_change_request
  return subscription_change_request.Base_redirect(keep_items=keep_items)
