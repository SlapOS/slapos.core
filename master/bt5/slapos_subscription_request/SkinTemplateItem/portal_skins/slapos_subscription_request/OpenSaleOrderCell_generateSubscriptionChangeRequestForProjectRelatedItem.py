from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

if activate_kw is None:
  activate_kw = {}

open_sale_order_cell = context
open_sale_order = open_sale_order_cell.getParentValue()
while open_sale_order.getPortalType() != 'Open Sale Order':
  open_sale_order = open_sale_order.getParentValue()

compute_node = open_sale_order_cell.getAggregateValue(portal_type=['Compute Node', 'Slave Instance', 'Software Instance'])
assert compute_node is not None

project = open_sale_order.getSourceProjectValue()
if project.getDestination() != open_sale_order.getDestination():
  # Project destination was probably modified.
  # Update the open order for Compute Node

  # Create the Compute Node's Subscription Change Request
  open_sale_order_cell.getResourceValue().Resource_createSubscriptionRequest(
    project.getDestinationValue(),
    # [software_type, software_release],
    open_sale_order_cell.getVariationCategoryList(),
    project,
    currency_value=open_sale_order.getPriceCurrencyValue(),
    portal_type='Subscription Change Request',
    item_value=compute_node,
    causality_value=open_sale_order,
    activate_kw=activate_kw
  )
