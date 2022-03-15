portal = context.getPortalObject()

root_trade_condition_reference_list = [
  "slapos_aggregated_trade_condition",
  "slapos_aggregated_subscription_trade_condition",
  # Valid trade condition for payments
  "slapos_manual_accounting_trade_condition"
]

root_trade_condition_list = portal.portal_catalog(
  portal_type="Sale Trade Condition",
  reference=root_trade_condition_reference_list,
  validation_state="validated",
)

specialise_uid_list = [x.getUid() for x in root_trade_condition_list]

if context.getSpecialiseUid() in specialise_uid_list:
  return True

return context.getSpecialiseUid() in [
    i.uid for i in portal.ERP5Site_searchRelatedInheritedSpecialiseList(
    portal_type="Sale Trade Condition",
    specialise_uid=specialise_uid_list,
    validation_state="validated")]
