portal = context.getPortalObject()
Base_translateString = portal.Base_translateString

from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

batch = (dialog_id is None)

# Search for the matching item
sql_instance_list = portal.portal_catalog(
  reference=reference,
  # Project are not handled yet, as it must also move all compute node subscription at the same time
  portal_type=['Instance Tree'],
  validation_state='validated',
  limit=2
)
if len(sql_instance_list) != 1:
  keep_items = {
    'your_reference': reference,
    'portal_status_level': 'warning',
    'portal_status_message': Base_translateString('Unknown reference')
  }
  if batch:
    raise ValueError(keep_items['portal_status_message'] + str(len(sql_instance_list)))
  return context.Base_renderForm(dialog_id, keep_items=keep_items)

# Search for the existing Open Sale Order
item = sql_instance_list[0].getObject()
open_sale_order_cell_list = portal.portal_catalog(
  portal_type=['Open Sale Order Line', 'Open Sale Order Cell'],
  aggregate__uid=item.getUid(),
  validation_state='validated',
  limit=2
)
if len(open_sale_order_cell_list) == 0:
  keep_items = {
    'your_reference': reference,
    'portal_status_level': 'warning',
    'portal_status_message': Base_translateString('No Open Sale Order found')
  }
  if batch:
    raise ValueError(keep_items['portal_status_message'])
  return context.Base_renderForm(dialog_id, keep_items=keep_items)
elif len(open_sale_order_cell_list) == 2:
  keep_items = {
    'your_reference': reference,
    'portal_status_level': 'warning',
    'portal_status_message': Base_translateString('Too many Open Sale Orders found')
  }
  if batch:
    raise ValueError(keep_items['portal_status_message'])
  return context.Base_renderForm(dialog_id, keep_items=keep_items)

open_sale_order_cell = open_sale_order_cell_list[0].getObject()
open_sale_order = open_sale_order_cell.getParentValue()
while open_sale_order.getPortalType() != 'Open Sale Order':
  open_sale_order = open_sale_order.getParentValue()

# Create the Subscription Change Request
subscription_change_request = open_sale_order_cell.getResourceValue().Resource_createSubscriptionRequest(
  context,
  # [software_type, software_release],
  open_sale_order_cell.getVariationCategoryList(),
  open_sale_order.getSourceProjectValue(),
  currency_value=open_sale_order.getPriceCurrencyValue(),
  portal_type='Subscription Change Request',
  item_value=item,
  causality_value=open_sale_order
)

if batch:
  return subscription_change_request
return subscription_change_request.Base_redirect()
