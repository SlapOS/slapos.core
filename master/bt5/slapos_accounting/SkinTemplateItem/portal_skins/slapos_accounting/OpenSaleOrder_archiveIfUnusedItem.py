open_sale_order = context

if open_sale_order.getValidationState() != 'validated':
  return

if open_sale_order.getLedger() != 'automated':
  raise ValueError('Can only archive automated open sale order')

for open_order_line in open_sale_order.contentValues(
  portal_type='Open Sale Order Line'
):
  content_list = open_order_line.contentValues()
  if len(content_list) == 0:
    content_list = [open_order_line]
  for open_order_cell in content_list:
    item = open_order_cell.getAggregateValue(portal_type=['Instance Tree', 'Compute Node', 'Project'])

    if item is None:
      raise AssertionError('No matching item on: %s' % open_order_cell.getRelativeUrl())

    elif item.getPortalType() == 'Instance Tree':
      if item.getSlapState() != 'destroy_requested':
        # Do not touch if the instance is still started/stopped
        return

    elif item.getPortalType() == 'Compute Node':
      # XXX TODO how to officially close a Compute Node
      #raise NotImplementedError('what is the finished state for Compute Node')
      return

    elif item.getPortalType() == 'Project':
      # Do not close project for now
      return

    else:
      raise KeyError('Unexpected portal type: %s on %s' % (item.getPortalType(), open_order_cell.getRelativeUrl()))

# if the script didn't return before, we can archive the open sale order
now = DateTime()
open_sale_order.edit(stop_date=now)
open_sale_order.archive(comment='No item in used anymore')

# Expand the open order one last time, to no miss any period
open_sale_order.activate().OpenOrder_updateSimulation()

return open_sale_order