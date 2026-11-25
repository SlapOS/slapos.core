web_site = context.getWebSectionValue()
assert web_site is not None

ticket = context
invoice_list = ticket.RegularisationRequest_getInvoiceList()

if not invoice_list:
  raise NotImplementedError('No invoice found')

return web_site.restrictedTraverse(invoice_list[0].getRelativeUrl()).Base_createExternalPaymentTransactionFromOutstandingAmountAndRedirect()
"""

# XXX XXX TODO rename InstanceTree_viewCreateDirectDepositPaymentTransactionOnSlaposPanelDialog to Item_viewCreateDirectDepositPaymentTransactionOnSlaposPanelDialog
if aggregate_value.getPortalType() == "Instance Tree":
  return web_site.restrictedTraverse(aggregate_value.getRelativeUrl()).Base_renderForm(
    'InstanceTree_viewCreateDirectDepositPaymentTransactionOnSlaposPanelDialog'
  )

raise NotImplementedError('Unsupported subscribed item: %s' % aggregate_value.getPortalType())
"""
