from erp5.component.module.DateUtils import getClosestDate

from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

consumption_change_request = context
assert consumption_change_request.getPortalType() == 'Consumption Change Request'
assert consumption_change_request.getSimulationState() == 'submitted'
consumption_change_request.reindexObject(activate_kw=activate_kw)

###############################################################################################
### Check the causality to change
previous_open_order = consumption_change_request.getCausalityValue(portal_type='Open Internal Order')

if previous_open_order is not None:
  # it must be an open sale order
  if previous_open_order.getValidationState() != 'validated':
    return consumption_change_request.cancel(comment='No Open Internal Order to update')

  # Search the line/cell
  open_order_movement = None
  open_order_movement_list = previous_open_order.contentValues(portal_type='Open Internal Order Line')
  if len(open_order_movement_list) == 1:
    open_order_movement = open_order_movement_list[0]
    open_order_movement_list = open_order_movement.contentValues(portal_type='Open Internal Order Cell')
    if 1 < len(open_order_movement_list):
      open_order_movement = None
    elif 1 == len(open_order_movement_list):
      open_order_movement = open_order_movement_list[0]

  if open_order_movement is None:
    return consumption_change_request.cancel(comment='Can not find the open order movement')
  previous_causality_to_compare = open_order_movement

else:
  return consumption_change_request.cancel(comment='Unknown causality')

###############################################################################################
### Check the supported scenario:
### - change instance tree owner
### - change project owner
### - change paying organisation (switch b2b)
### - change payable to free
### - change free to payable
### - change payable price
### - change trade condition version

identical_order_base_category_list = [
  'destination',
  'destination_section',
  'destination_decision',
  'destination_project',
  # 'resource',
  # 'variation_category_list',
  # 'quantity_unit',
  'quantity',
  'ledger',
  'source',
  'source_section',
  'source_project',
  'price_currency',
  'price'
  'specialise'
]
edit_kw = {
  'causality': consumption_change_request.getRelativeUrl()
}

if previous_causality_to_compare.getResource() != consumption_change_request.getResource():
  # change resource
  edit_kw['resource'] = consumption_change_request.getResource(None)
  edit_kw['variation_category_list'] = consumption_change_request.getVariationCategoryList()
  edit_kw['quantity_unit'] = consumption_change_request.getQuantityUnit()

else:
  return consumption_change_request.cancel(comment='Unsupported resource changes')


###############################################################################################
### Check that other properties do not contain unexpected changes
for changed_key, changed_value in edit_kw.items():
  if changed_value is None:
    # Ensure new values are not empty
    return consumption_change_request.cancel(comment='Unhandled empty changes on: %s' % changed_key)

for identical_order_base_category in identical_order_base_category_list:
  edit_kw[identical_order_base_category] = consumption_change_request.getProperty(identical_order_base_category)
  if previous_causality_to_compare.getProperty(identical_order_base_category) != edit_kw[identical_order_base_category]:
    return consumption_change_request.cancel(comment='Unhandled requested changes on: %s' % identical_order_base_category)

# Ensure the subscribed item is the same
# (done separatly, because open order cell have multiple aggregated items
subscribed_item = previous_causality_to_compare.getAggregateValue(portal_type=['Software Instance', 'Slave Instance', 'Compute Node'])
if consumption_change_request.getAggregateUid() == subscribed_item.getUid():
  edit_kw['aggregate'] = consumption_change_request.getAggregate()
else:
  return consumption_change_request.cancel(comment='Unhandled requested changes on: aggregate')


###############################################################################################
### Create the new Subscription Request

new_open_order = subscribed_item.Item_createOpenInternalOrder(default_service=consumption_change_request.getResource())
if new_open_order is None:
  return consumption_change_request.cancel(comment='Could not create new open order')

# Compensation
if previous_open_order:
  current_date = getClosestDate(target_date=new_open_order.getStartDate(), precision='day')
  previous_open_order.OpenInternalOrderLine_archiveIfUnusedItem(check_unused_item=False)
  # if we want to always activate a discount as soon as an open order is archived (outside subscription change request)
  # it is needed to call OpenSaleOrderCell_createDiscountSalePackingList is an interaction workflow
  # with more extra checks.
  open_order_movement.OpenInternalOrderCell_createDiscountInternalPackingList(
    current_date,
    'transfer discount from %s to %s' % (previous_open_order.getReference(), new_open_order.getReference()),
    consumption_change_request
  )#, activate_kw=activate_kw)
else:
  raise NotImplementedError('Do not know how to compensate')

consumption_change_request.validate()
consumption_change_request.invalidate(comment='New open order: %s' % new_open_order.getRelativeUrl())
return new_open_order
