aggregate_value = context.getAggregateValue()

if aggregate_value.getPortalType() == "Instance Tree":
  return aggregate_value.Base_redirect(
    'InstanceTree_viewCreateDirectDepositPaymentTransactionOnSlaposPanelDialog'
  )

return context.getPortalObject().accounting_module.Base_redirect(
  "AccountingTransactionModule_viewCreateExternalPaymentTransactionOnSlaposPanelDialog")
