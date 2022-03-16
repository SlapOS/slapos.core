root_trade_condition_reference_list = [
  "slapos_aggregated_trade_condition",
  "slapos_aggregated_subscription_trade_condition",
  # Valid trade condition for payments
  "slapos_manual_accounting_trade_condition"
]
return context.Base_useSaleTradeConditionReference(root_trade_condition_reference_list)
