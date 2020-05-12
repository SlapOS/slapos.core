# Search by SPL for the first period
portal = context.getPortalObject()

reservation_fee_invoice = context.getCausalityValue(
  portal_type="Sale Invoice Transaction"
)

reservation_fee_total_price = reservation_fee_invoice.getTotalPrice()
subscription_request_total_price = context.getPrice() * context.getQuantity()

remaining_to_pay = subscription_request_total_price - reservation_fee_total_price

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
      if payment.getSimulationState() in ["stopped", "delivered"]:
        # Invoice is already paied so we just move foward
        return payment
      elif payment.getSimulationState() in ["started"]:
        payment_total_price = payment.PaymentTransaction_getTotalPayablePrice()
        if not(round(payment_total_price, 2) + round(remaining_to_pay, 2)):
          # Payment contains the expected value
          return payment

# Payment isn't ready
return
