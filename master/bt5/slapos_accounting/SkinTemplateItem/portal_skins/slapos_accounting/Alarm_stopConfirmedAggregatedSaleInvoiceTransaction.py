from DateTime import DateTime
portal = context.getPortalObject()

portal.portal_catalog.searchAndActivate(
  portal_type='Sale Invoice Transaction',
  simulation_state='confirmed',
  causality_state='solved',
  ledger__uid=portal.portal_categories.ledger.automated.getUid(),
  method_id='Delivery_stopConfirmedAggregatedSaleInvoiceTransaction',
  activate_kw={'tag': tag}
)
context.activate(after_tag=tag).getId()
