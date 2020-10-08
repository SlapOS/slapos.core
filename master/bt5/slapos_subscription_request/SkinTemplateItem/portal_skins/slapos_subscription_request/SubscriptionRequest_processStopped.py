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
    for payment in invoice.getCausalityRelatedValueList(
      portal_type=["Payment Transaction", "Sale Invoice Transaction"]):
      if payment.getSimulationState() not in ["confirmed", "started"]:
        if round(payment.PaymentTransaction_getTotalPayablePrice(), 2) == 0.0:
          continue
        return

# No open Payments pending.
context.deliver()
