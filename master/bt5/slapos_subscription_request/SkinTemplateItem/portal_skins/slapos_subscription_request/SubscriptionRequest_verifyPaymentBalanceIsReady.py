# Search by SPL for the first period
portal = context.getPortalObject()

reservation_fee_invoice = context.getCausalityValue(
  portal_type="Sale Invoice Transaction"
)
if reservation_fee_invoice is None:
  return

specialise_uid = portal.restrictedTraverse(
    portal.portal_preferences.getPreferredAggregatedSubscriptionSaleTradeCondition()).getUid()

trade_condition_uid_list = [specialise_uid]
trade_condition_uid_list.extend([
    i.uid for i in portal.portal_catalog(
    portal_type="Sale Trade Condition",
    specialise__uid=specialise_uid,
    validation_state="validated")])

# This is normally one, but we navegate in case
for packing_list in portal.portal_catalog(
  portal_type="Sale Packing List",
  causality_uid=context.getUid(),
  specialise_uid=trade_condition_uid_list
  ):
  for invoice in packing_list.getCausalityRelatedValueList(
    portal_type="Sale Invoice Transaction"):
    for payment in invoice.getCausalityRelatedValueList(
      portal_type=["Payment Transaction", "Sale Invoice Transaction"]):
      if payment.getSimulationState() in ["stopped", "delivered", "started"]:
        # Invoice is already paied so we just move foward
        if not payment.checkConsistency():
          return payment

# Payment isn't ready
return
