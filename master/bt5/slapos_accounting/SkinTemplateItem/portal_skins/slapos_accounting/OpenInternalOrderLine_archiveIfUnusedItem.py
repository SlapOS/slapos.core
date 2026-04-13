from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

open_internal_order = context
while open_internal_order.getPortalType() != 'Open Internal Order':
  open_internal_order = open_internal_order.getParentValue()

if open_internal_order.getValidationState() != 'validated':
  return

if open_internal_order.getLedger() != 'automated':
  raise ValueError('Can only archive automated open sale order')

for open_order_line in open_internal_order.contentValues(
  portal_type='Open Internal Order Line'
):
  content_list = open_order_line.contentValues()
  if len(content_list) == 0:
    content_list = [open_order_line]
  for open_order_cell in content_list:
    item = open_order_cell.getAggregateValue(portal_type=['Compute Node', 'Software Instance', 'Slave Instance'])
    hosting_subscription = open_order_cell.getAggregateValue(portal_type='Consumption Subscription')

    if item is None:
      raise AssertionError('No matching item on: %s' % open_order_cell.getRelativeUrl())

    if (item.getValidationState() not in ['invalidated', 'archived']):
      # Do not touch if the item is not clean yet
      return

    hosting_subscription.archive(comment='No item in used anymore')

# if the script didn't return before, we can archive the open sale order
now = DateTime()
open_internal_order.edit(stop_date=now)
open_internal_order.archive(comment='No item in used anymore')

# Expand the open order one last time, to no miss any period
open_internal_order.activate().OpenOrder_updateSimulation()

return open_internal_order
