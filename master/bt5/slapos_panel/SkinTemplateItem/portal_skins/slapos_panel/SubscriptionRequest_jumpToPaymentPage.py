aggregate_value = context.getAggregateValue()
web_site = context.getWebSectionValue()
assert web_site is not None

# XXX XXX TODO rename InstanceTree_viewCreateDirectDepositPaymentTransactionOnSlaposPanelDialog to Item_viewCreateDirectDepositPaymentTransactionOnSlaposPanelDialog
if aggregate_value.getPortalType() == "Instance Tree":
  return web_site.restrictedTraverse(aggregate_value.getRelativeUrl()).Base_renderForm(
    'InstanceTree_viewCreateDirectDepositPaymentTransactionOnSlaposPanelDialog'
  )

raise NotImplementedError('Unsupported subscribed item: %s' % aggregate_value.getPortalType())
