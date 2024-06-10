from erp5.component.module.DateUtils import getClosestDate

from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

subscription_change_request = context
portal = context.getPortalObject()
assert subscription_change_request.getPortalType() == 'Subscription Change Request'
assert subscription_change_request.getSimulationState() == 'submitted'

subscription_change_request.reindexObject(activate_kw=activate_kw)

def invalidate(document, comment):
  context.validate()
  context.invalidate(comment=comment)

# Subscription Change Request will change an ongoing Open Sale Order
open_sale_order = subscription_change_request.getCausalityValue(portal_type='Open Sale Order')
if (open_sale_order is None) or (open_sale_order.getValidationState() != 'validated'):
  return invalidate(subscription_change_request, 'No Open Sale Order to update')

# Search the line/cell
open_order_movement = None
open_order_movement_list = open_sale_order.contentValues(portal_type='Open Sale Order Line')
if len(open_order_movement_list) == 1:
  open_order_movement = open_order_movement_list[0]
  open_order_movement_list = open_order_movement.contentValues(portal_type='Open Sale Order Cell')
  if 1 < len(open_order_movement_list):
    open_order_movement = None
  elif 1 == len(open_order_movement_list):
    open_order_movement = open_order_movement_list[0]

if open_order_movement is None:
  return invalidate(subscription_change_request, 'Can not find the open order movement')

identical_order_base_category_list = [
  'specialise',
  # 'destination',
  # 'destination_section',
  # 'destination_decisition',
  'destination_project',
  'source',
  'source_section',
  'source_project',
  'price_currency',

  'resource',
  'variation_category_list',
  'quantity_unit',

  'quantity',
  'price'
]
for identical_order_base_category in identical_order_base_category_list:
  if open_order_movement.getProperty(identical_order_base_category) != subscription_change_request.getProperty(identical_order_base_category):
    return invalidate(subscription_change_request, 'Unhandled requested changes on: %s' % identical_order_base_category)

# Ensure the subscribed item is the same
subscribed_item = open_order_movement.getAggregateValue(portal_type=['Instance Tree', 'Compute Node', 'Project'])
if subscription_change_request.getAggregateUid() != subscribed_item.getUid():
  return invalidate(subscription_change_request, 'Unhandled requested changes on: aggregate')

# Ensure destination is different
if subscription_change_request.getDestination() == open_sale_order.getDestination():
  return invalidate(subscription_change_request, 'Expected change on: destination')

# Change Subscripted Item user if needed
subscribed_item = open_order_movement.getAggregateValue(portal_type=['Instance Tree', 'Compute Node', 'Project'])
if subscribed_item is None:
  raise NotImplementedError('Unsupported subscribed item')
elif subscribed_item.getPortalType() == 'Compute Node':
  # No user is set on Compute Node
  pass
elif subscribed_item.getPortalType() == 'Instance Tree':
  # Check if user does not already have a instance tree with the same title
  # to prevent breaking slapos's request
  existing_instance_tree = portal.portal_catalog.getResultValue(
    portal_type='Instance Tree',
    title={'query': subscribed_item.getTitle(), 'key': 'ExactMatch'},
    destination_section__uid=subscription_change_request.getDestinationUid()
  )
  if existing_instance_tree is not None:
    return invalidate(subscription_change_request, 'Instance Tree with the same title found: %s' % existing_instance_tree.getRelativeUrl())

  subscribed_item.edit(destination_section=subscription_change_request.getDestination())
elif subscribed_item.getPortalType() == 'Project':
  subscribed_item.edit(destination=subscription_change_request.getDestination())
else:
  raise NotImplementedError('Not implemented subscribed item')

# Create new Open Sale Order
next_open_sale_order = subscription_change_request.SubscriptionRequest_createOpenSaleOrder()
current_date = getClosestDate(target_date=next_open_sale_order.getCreationDate(), precision='day')

# XXX Compensation
open_sale_order.OpenSaleOrder_archiveIfUnusedItem(check_unused_item=False)
# if we want to always activate a discount as soon as an open order is archived (outside subscription change request)
# it is needed to call OpenSaleOrderCell_createDiscountSalePackingList is an interaction workflow
# with more extra checks.
open_order_movement.OpenSaleOrderCell_createDiscountSalePackingList(
  current_date,
  'transfer discount from %s to %s' % (open_sale_order.getReference(), next_open_sale_order.getReference()),
  subscription_change_request
)#, activate_kw=activate_kw)

return invalidate(subscription_change_request, 'New open order: %s' % next_open_sale_order.getRelativeUrl())
