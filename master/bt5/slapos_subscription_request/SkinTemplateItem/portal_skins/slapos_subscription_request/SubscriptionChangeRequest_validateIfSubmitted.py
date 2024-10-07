from erp5.component.module.DateUtils import getClosestDate

from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

subscription_change_request = context
portal = context.getPortalObject()
assert subscription_change_request.getPortalType() == 'Subscription Change Request'
assert subscription_change_request.getSimulationState() == 'submitted'

###############################################################################################
### Check the causality to change

previous_subscription_request = subscription_change_request.getCausalityValue(portal_type='Subscription Request')
previous_open_order = subscription_change_request.getCausalityValue(portal_type='Open Sale Order')

if previous_subscription_request is not None:
  # it will be an subscription request
  if previous_subscription_request.getSimulationState() != 'submitted':
    return subscription_change_request.cancel(comment='Can only change submitted Subscription Request')
  previous_causality_to_compare = previous_subscription_request

elif previous_open_order is not None:
  # it must be an open sale order
  if previous_open_order.getValidationState() != 'validated':
    return subscription_change_request.cancel(comment='No Open Sale Order to update')

  # Search the line/cell
  open_order_movement = None
  open_order_movement_list = previous_open_order.contentValues(portal_type='Open Sale Order Line')
  if len(open_order_movement_list) == 1:
    open_order_movement = open_order_movement_list[0]
    open_order_movement_list = open_order_movement.contentValues(portal_type='Open Sale Order Cell')
    if 1 < len(open_order_movement_list):
      open_order_movement = None
    elif 1 == len(open_order_movement_list):
      open_order_movement = open_order_movement_list[0]

  if open_order_movement is None:
    return subscription_change_request.cancel(comment='Can not find the open order movement')
  previous_causality_to_compare = open_order_movement

else:
  return subscription_change_request.cancel(comment='Unknown causality')

###############################################################################################
### Check the supported scenario:
### - change instance tree owner
### - change paying organisation (switch b2b)
### - change payable to free
### - change payable price

identical_order_base_category_list = [
  # 'destination',
  # 'destination_section',
  # 'destination_decision',
  'destination_project',
  'resource',
  'variation_category_list',
  'quantity_unit',
  'quantity',
  'ledger',
  'source',
  # 'source_section',
  'source_project',
  'price_currency',
  # 'price'
  # 'specialise'
]
edit_kw = {
  'causality': subscription_change_request.getRelativeUrl()
}
is_owner_change_needed = False

if previous_causality_to_compare.getDestination() != subscription_change_request.getDestination():
  # change instance tree owner
  identical_order_base_category_list.extend(['source_section', 'price'])
  edit_kw['destination'] = subscription_change_request.getDestination(None)
  edit_kw['destination_section'] = subscription_change_request.getDestinationSection()
  edit_kw['destination_decision'] = subscription_change_request.getDestinationDecision()
  edit_kw['specialise'] = subscription_change_request.getSpecialise(None)
  is_owner_change_needed = True

elif previous_causality_to_compare.getDestinationSection() != subscription_change_request.getDestinationSection():
  # change paying organisation (switch b2b)
  identical_order_base_category_list.extend(['destination', 'destination_decision', 'source_section', 'price'])
  edit_kw['destination_section'] = subscription_change_request.getDestinationSection()
  edit_kw['specialise'] = subscription_change_request.getSpecialise()

elif (previous_causality_to_compare.getSourceSection(None) is not None) and \
     (previous_causality_to_compare.getPrice() != subscription_change_request.getPrice()):
  # change a payable price
  identical_order_base_category_list.extend(['destination', 'destination_section', 'destination_decision'])
  edit_kw['price'] = subscription_change_request.getPrice()
  edit_kw['specialise'] = subscription_change_request.getSpecialise()

  if 0 < subscription_change_request.getPrice():
    # change the price
    identical_order_base_category_list.extend(['source_section'])

  else:
    # change to free
    if subscription_change_request.getSourceSection() is not None:
      return subscription_change_request.cancel(comment='Can only change payable Subscription Request to free')

else:
  return subscription_change_request.cancel(comment='Unsupported changes')


###############################################################################################
### Check that other properties do not contain unexpected changes
for changed_key, changed_value in edit_kw.items():
  if changed_value is None:
    # Ensure new values are not empty
    return subscription_change_request.cancel(comment='Unhandled requested changes on: %s' % changed_key)

for identical_order_base_category in identical_order_base_category_list:
  edit_kw[identical_order_base_category] = subscription_change_request.getProperty(identical_order_base_category)
  if previous_causality_to_compare.getProperty(identical_order_base_category) != edit_kw[identical_order_base_category]:
    return subscription_change_request.cancel(comment='Unhandled requested changes on: %s' % identical_order_base_category)

# Ensure the subscribed item is the same
# (done separatly, because open order cell have multiple aggregated items
subscribed_item = previous_causality_to_compare.getAggregateValue(portal_type=['Instance Tree', 'Compute Node', 'Project'])
if subscription_change_request.getAggregateUid() == subscribed_item.getUid():
  edit_kw['aggregate'] = subscription_change_request.getAggregate()
else:
  return subscription_change_request.cancel(comment='Unhandled requested changes on: aggregate')


###############################################################################################
### change item owner if needed
if is_owner_change_needed:
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
      validation_state='validated',
      destination_section__uid=subscription_change_request.getDestinationUid()
    )
    if existing_instance_tree is not None:
      return subscription_change_request.cancel(comment='Instance Tree with the same title found: %s' % existing_instance_tree.getRelativeUrl())

    subscribed_item.edit(destination_section=subscription_change_request.getDestination())
  elif subscribed_item.getPortalType() == 'Project':
    subscribed_item.edit(destination=subscription_change_request.getDestination())
  else:
    raise NotImplementedError('Not implemented subscribed item')


###############################################################################################
### Create the new Subscription Request

portal_type = 'Subscription Request'
new_subscription_request = portal.getDefaultModuleValue(portal_type).newContent(
  portal_type=portal_type,
  # follow Resource_createSubscriptionRequest
  start_date=subscription_change_request.getStartDate(),
  effective_date=subscription_change_request.getEffectiveDate(),
  activate_kw=activate_kw,
  **edit_kw
)
new_subscription_request.submit(comment='Replacing %s' % subscription_change_request.getRelativeUrl())

# Compensation
if previous_subscription_request:
  previous_subscription_request.cancel(comment='Replaced by %s' % new_subscription_request.getRelativeUrl())
  previous_subscription_request.reindexObject(activate_kw=activate_kw)
elif previous_open_order:
  current_date = getClosestDate(target_date=new_subscription_request.getCreationDate(), precision='day')
  previous_open_order.OpenSaleOrder_archiveIfUnusedItem(check_unused_item=False)
  # if we want to always activate a discount as soon as an open order is archived (outside subscription change request)
  # it is needed to call OpenSaleOrderCell_createDiscountSalePackingList is an interaction workflow
  # with more extra checks.
  open_order_movement.OpenSaleOrderCell_createDiscountSalePackingList(
    current_date,
    'transfer discount from %s to %s' % (previous_open_order.getReference(), new_subscription_request.getReference()),
    subscription_change_request
  )#, activate_kw=activate_kw)
else:
  raise NotImplementedError('Do not know how to compensate')


subscription_change_request.reindexObject(activate_kw=activate_kw)
subscription_change_request.validate()
return subscription_change_request.invalidate(comment='New subscription request: %s' % new_subscription_request.getRelativeUrl())
