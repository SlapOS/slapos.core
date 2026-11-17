aggregate_value = context.getAggregateValue()
web_site = context.getWebSectionValue()
assert web_site is not None

if aggregate_value.getPortalType() == "Instance Tree":
  return web_site.restrictedTraverse(aggregate_value.getRelativeUrl()).Base_renderForm(
    'InstanceTree_viewCreateDirectDepositPaymentTransactionOnSlaposPanelDialog'
  )

return web_site.restrictedTraverse('accounting_module').Base_renderForm(
  "AccountingTransactionModule_viewCreateExternalPaymentTransactionOnSlaposPanelDialog")
