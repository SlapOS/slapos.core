from zExceptions import Unauthorized

if REQUEST is not None:
  raise Unauthorized

sale_trade_condition = context
is_compute_node_trade_condition_type = (
  (sale_trade_condition.getTradeConditionType() == 'compute_node') and
  (sale_trade_condition.getExpirationDate(None) is None)
)

error_list = []

if is_compute_node_trade_condition_type:

  error_list.append('trade_condition_type/compute_node must expire')
  if fixit:
    sale_trade_condition.SaleTradeCondition_archiveIfComputeNodeTradeConditionType()

return error_list
