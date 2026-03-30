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


# if the script didn't return before, we can archive the open sale order
now = DateTime()
open_sale_order.edit(stop_date=now, activate_kw=activate_kw)
open_sale_order.archive(comment='Archiving compute node trade condition type')

# Expand the open order one last time, to no miss any period
open_sale_order.activate(activate_kw=activate_kw).OpenOrder_updateSimulation()

return open_sale_order
