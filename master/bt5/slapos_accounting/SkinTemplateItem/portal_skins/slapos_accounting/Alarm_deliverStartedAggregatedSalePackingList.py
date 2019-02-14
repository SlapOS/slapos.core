portal = context.getPortalObject()

specialise_uid = [portal.restrictedTraverse(portal.portal_preferences.getPreferredAggregatedSaleTradeCondition()).getUid(),
                  portal.restrictedTraverse(portal.portal_preferences.getPreferredAggregatedSubscriptionSaleTradeCondition()).getUid()]
portal.portal_catalog.searchAndActivate(
  portal_type='Sale Packing List',
  simulation_state='started',
  causality_state='solved',
  specialise_uid=specialise_uid,
  method_id='Delivery_deliverStartedAggregatedSalePackingList',
  activate_kw={'tag': tag},
)
context.activate(after_tag=tag).getId()
