from DateTime import DateTime
portal = context.getPortalObject()


trade_condition_uid_list = []
# search for user specific trade conditions 
root_trade_condition_uid_list = [
  portal.restrictedTraverse(
    portal.portal_preferences.getPreferredAggregatedSubscriptionSaleTradeCondition()).getUid(),
  portal.restrictedTraverse(
    portal.portal_preferences.getPreferredAggregatedSaleTradeCondition()).getUid()]

trade_condition_uid_list.extend(root_trade_condition_uid_list)
trade_condition_uid_list.extend([
  i.uid for i in portal.ERP5Site_searchRelatedInheritedSpecialiseList(
  portal_type="Sale Trade Condition",
  specialise_uid=root_trade_condition_uid_list,
  validation_state="validated")])

portal.portal_catalog.searchAndActivate(
  portal_type='Sale Invoice Transaction',
  simulation_state='confirmed',
  causality_state='solved',
  specialise__uid=trade_condition_uid_list,
  method_id='Delivery_stopConfirmedAggregatedSaleInvoiceTransaction',
  activate_kw={'tag': tag}
)
context.activate(after_tag=tag).getId()
