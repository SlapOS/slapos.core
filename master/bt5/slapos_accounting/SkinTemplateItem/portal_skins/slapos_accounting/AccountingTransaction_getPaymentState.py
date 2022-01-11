simulation_state = context.getSimulationState()

if simulation_state in ("cancelled", "deleted", "draft"):
  result = "Cancelled"

elif simulation_state in ("planned", "confirmed", "ordered", "started"):
  result = "Ongoing"

else:
  portal = context.getPortalObject()
  person = portal.portal_membership.getAuthenticatedMember().getUserValue()

  paid = context.SaleInvoiceTransaction_isLettered()

  if paid:
    result = "Paid"
  elif context.getTotalPrice() == 0:
    result = "Free!"
  else:
    result = "Pay Now"

    # Search to know if there are some payment waiting for confirmation
    payment = portal.portal_catalog.getResultValue(
      portal_type="Payment Transaction",
      simulation_state="started",
      causality__uid=context.getUid()
    )
    if payment is not None:
      # Check if mapping exists
      if person is not None:
        external_payment_id = person.Person_restrictMethodAsShadowUser(
          shadow_document=person,
          callable_object=payment.PaymentTransaction_getExternalPaymentId,
          argument_list=[])[0]
      else:
        external_payment_id = payment.PaymentTransaction_getExternalPaymentId()

      if external_payment_id is not None:
        result = "Waiting for payment confirmation"

return result
