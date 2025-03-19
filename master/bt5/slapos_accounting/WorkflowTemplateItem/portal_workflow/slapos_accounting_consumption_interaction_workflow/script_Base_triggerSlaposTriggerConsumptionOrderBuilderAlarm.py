sale_packing_list = state_change['object']
trade_condition = sale_packing_list.getSpecialiseValue()

if trade_condition is not None and trade_condition.getTradeConditionType() == 'consumption':
  return sale_packing_list.Base_reindexAndSenseAlarm(['slapos_trigger_consumption_order_builder'])
