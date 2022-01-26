if params is None:
  params = {}

from DateTime import DateTime
portal = context.getPortalObject()

trade_condition_uid_list = []
root_trade_condition_value = portal.restrictedTraverse(
    portal.portal_preferences.getPreferredAggregatedSubscriptionSaleTradeCondition())
    
root_trade_condition_uid = root_trade_condition_value.getUid()

trade_condition_uid_list.append(root_trade_condition_uid)
trade_condition_uid_list.extend([
  i.uid for i in portal.ERP5Site_searchRelatedInheritedSpecialiseList(
  portal_type=root_trade_condition_value.getPortalType(),
  specialise_uid=root_trade_condition_uid,
  validation_state="validated")])

portal.portal_catalog.searchAndActivate(
  portal_type='Sale Packing List',
  simulation_state='confirmed',
  causality_state='solved',
  specialise__uid=trade_condition_uid_list,
  method_id='Delivery_startConfirmedAggregatedSalePackingList',
  activate_kw={'tag': tag},
)
context.activate(after_tag=tag).getId()
