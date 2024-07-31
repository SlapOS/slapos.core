portal = context.getPortalObject()
Base_translateString = portal.Base_translateString
organisation = context

from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

batch = (dialog_id is None)

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
tag = "%s-%s" % (script.id, subscription_request.getRelativeUrl())

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
  temp_object=True,
  item_value=item,
  causality_value=subscription_request.getCausalityValue()
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
    # source_project=current_trade_condition.getSourceProject(),
    price_currency=current_trade_condition.getPriceCurrency(),
    trade_condition_type=current_trade_condition.getTradeConditionType(),
  )
  new_sale_trade_condition.validate()
  new_sale_trade_condition.reindexObject(activate_kw={'tag': tag})
  organisation.activate(after_tag=tag).Organisation_claimSlaposSubscriptionRequest(reference, None)
  keep_items = {
    'portal_status_message': Base_translateString('Creating a dedicated Trade Condition for the customer')
  }
  if batch:
    return new_sale_trade_condition
  return new_sale_trade_condition.Base_redirect(keep_items=keep_items)

elif ((current_trade_condition.getDestination() == subscription_request.getDestination()) and
      (current_trade_condition.getDestinationSection() == organisation.getRelativeUrl())):
  # We have a matching Trade Condition.
  # We can recreate the Subscription Request
  subscription_change_request = subscription_request.getResourceValue().Resource_createSubscriptionRequest(
    subscription_request.getDestinationValue(),
    # [software_type, software_release],
    subscription_request.getVariationCategoryList(),
    project,
    currency_value=subscription_request.getPriceCurrencyValue(),
    item_value=item,
    causality_value=subscription_request.getCausalityValue()
  )
  assert subscription_change_request.getDestinationSection() == organisation.getRelativeUrl()
  subscription_request.cancel(comment='Replaced by %s' % subscription_change_request.getReference())

  if batch:
    return subscription_change_request
  return subscription_change_request.Base_redirect()


else:
  keep_items = {
    'your_reference': reference,
    'portal_status_level': 'error',
    'portal_status_message': Base_translateString('This customer already has a dedicated incompatible Trade Condition')
  }
  if batch:
    raise ValueError(keep_items['portal_status_message'])
  return current_trade_condition.Base_redirect(keep_items=keep_items)
