portal = context.getPortalObject()

trade_condition_uid_list = []
root_trade_condition_uid_list = [
  portal.restrictedTraverse(
    portal.portal_preferences.getPreferredAggregatedSubscriptionSaleTradeCondition()).getUid(),
  portal.restrictedTraverse(
    portal.portal_preferences.getPreferredAggregatedSaleTradeCondition()).getUid()]

trade_condition_uid_list.extend(root_trade_condition_uid_list)
trade_condition_uid_list.extend([
      i.uid for i in portal.ERP5Site_searchRelatedInheritedSpecialiseList(
      specialise_uid=root_trade_condition_uid_list,
      validation_state="validated")])

portal.portal_catalog.searchAndActivate(
  portal_type='Sale Packing List',
  simulation_state='started',
  causality_state='solved',
  specialise_uid=trade_condition_uid_list,
  method_id='Delivery_deliverStartedAggregatedSalePackingList',
  activate_kw={'tag': tag},
)
context.activate(after_tag=tag).getId()
