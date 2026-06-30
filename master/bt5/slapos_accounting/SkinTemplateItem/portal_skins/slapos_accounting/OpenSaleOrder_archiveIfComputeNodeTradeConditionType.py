from zExceptions import Unauthorized

if REQUEST is not None:
  raise Unauthorized

tag = tag or script.id
activate_kw = {'tag': tag}
open_sale_order = context

if open_sale_order.getValidationState() != 'validated':
  return

if open_sale_order.getLedger() != 'automated':
  raise ValueError('Can only archive automated open sale order')

is_compute_node_trade_condition_type = False
trade_condition = open_sale_order.getSpecialiseValue(portal_type='Sale Trade Condition')
while trade_condition is not None:
  if trade_condition.getTradeConditionType() == 'compute_node':
    is_compute_node_trade_condition_type = True
    break
  else:
    trade_condition = trade_condition.getSpecialiseValue(portal_type='Sale Trade Condition')

if not is_compute_node_trade_condition_type:
  return

for open_order_line in open_sale_order.contentValues(
  portal_type='Open Sale Order Line'
):
  content_list = open_order_line.contentValues()
  if len(content_list) == 0:
    content_list = [open_order_line]
  for open_order_cell in content_list:
    item = open_order_cell.getAggregateValue(portal_type=['Compute Node'])
    hosting_subscription = open_order_cell.getAggregateValue(portal_type='Hosting Subscription')

    if item is None:
      raise AssertionError('No matching item on: %s' % open_order_cell.getRelativeUrl())

    hosting_subscription.archive(comment='Archiving compute node trade condition type')
    hosting_subscription.reindexObject(activate_kw=activate_kw)

# if the script didn't return before, we can archive the open sale order
now = DateTime()
open_sale_order.edit(stop_date=now, activate_kw=activate_kw)
open_sale_order.archive(comment='Archiving compute node trade condition type')

# Expand the open order one last time, to no miss any period
open_sale_order.activate(activate_kw=activate_kw).OpenOrder_updateSimulation()

return open_sale_order
