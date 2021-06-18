root_trade_condition_list = ["sale_trade_condition_module/slapos_aggregated_trade_condition",
                             "sale_trade_condition_module/slapos_aggregated_subscription_trade_condition"]

if context.getSpecialise() in root_trade_condition_list:
  return True

portal = context.getPortalObject()
specialise_uid = [
  portal.restrictedTraverse(i).getUid() for i in root_trade_condition_list
]

return context.getSpecialiseUid() in [
    i.uid for i in portal.portal_catalog(
    portal_type="Sale Trade Condition",
    specialise__uid=specialise_uid,
    validation_state="validated")]
