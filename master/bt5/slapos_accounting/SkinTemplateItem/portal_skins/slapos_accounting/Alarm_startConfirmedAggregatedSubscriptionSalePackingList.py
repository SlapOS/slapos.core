if params is None:
  params = {}

from DateTime import DateTime

portal = context.getPortalObject()
portal.portal_catalog.searchAndActivate(
  portal_type='Sale Packing List',
  simulation_state='confirmed',
  causality_state='solved',
  specialise_uid=portal.restrictedTraverse(
    portal.portal_preferences.getPreferredAggregatedSubscriptionSaleTradeCondition()).getUid(),
  method_id='Delivery_startConfirmedAggregatedSalePackingList',
  activate_kw={'tag': tag},
)
context.activate(after_tag=tag).getId()
