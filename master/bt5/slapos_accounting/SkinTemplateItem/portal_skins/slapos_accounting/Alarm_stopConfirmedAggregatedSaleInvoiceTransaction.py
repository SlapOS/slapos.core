from DateTime import DateTime

portal = context.getPortalObject()
specialise_uid = [portal.restrictedTraverse(portal.portal_preferences.getPreferredAggregatedSaleTradeCondition()).getUid(),
                  portal.restrictedTraverse(portal.portal_preferences.getPreferredAggregatedSubscriptionSaleTradeCondition()).getUid()]
portal.portal_catalog.searchAndActivate(
  portal_type='Sale Invoice Transaction',
  simulation_state='confirmed',
  causality_state='solved',
  specialise_uid=specialise_uid,
  method_id='Delivery_stopConfirmedAggregatedSaleInvoiceTransaction',
  activate_kw={'tag': tag}
)
context.activate(after_tag=tag).getId()
