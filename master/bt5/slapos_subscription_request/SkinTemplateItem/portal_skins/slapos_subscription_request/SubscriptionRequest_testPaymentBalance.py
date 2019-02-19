# Search by SPL for the first period
portal = context.getPortalObject()

# This is normally one, but we navegate in case
for packing_list in portal.portal_catalog(
  portal_type="Sale Packing List",
  causality_uid=context.getUid(),
  specialise_uid=portal.restrictedTraverse(
    portal.portal_preferences.getPreferredAggregatedSubscriptionSaleTradeCondition()).getUid(),
  ):
  for invoice in packing_list.getCausalityRelatedValueList(
    portal_type="Sale Invoice Transaction"):
    payment = invoice.getCausalityRelatedValue(
      portal_type="Payment Transaction")
    if payment is not None and payment.getSimulationState() in ["stopped", "delivered"]:
      return True

return False
