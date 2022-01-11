simulation_state = context.getSimulationState()

if simulation_state in ("cancelled", "deleted", "draft"):
  result = "Cancelled"

elif simulation_state in ("planned", "confirmed", "ordered", "started"):
  result = "Ongoing"

else:
  portal = context.getPortalObject()

  person = portal.portal_membership.getAuthenticatedMember().getUserValue()
  paid = True

  def isNodeFromLineReceivable(line):
    node_value = line.getSourceValue(portal_type='Account')
    return node_value.getAccountType() == 'asset/receivable'

  for line in context.getMovementList(portal.getPortalAccountingMovementTypeList()):
    if person is not None:
      is_node_from_line_receivable = person.Person_restrictMethodAsShadowUser(
        shadow_document=person,
        callable_object=isNodeFromLineReceivable,
        argument_list=[line])
    else:
      is_node_from_line_receivable = isNodeFromLineReceivable(line)
 
    if is_node_from_line_receivable:
      if not line.hasGroupingReference():
        paid = False
        break

  reversal = portal.portal_catalog.getResultValue(
      portal_type="Sale Invoice Transaction",
      simulation_state="stopped",
      default_causality_uid=context.getUid()
    )
  if reversal is not None and (context.getTotalPrice() + reversal.getTotalPrice()) == 0:
    result = "Cancelled"
  elif paid:
    result = "Paid"
  elif context.getTotalPrice() == 0:
    result = "Free!"
  else:
    result = "Pay Now"

    # Search to know if there are some payment waiting for confirmation
    payment = portal.portal_catalog.getResultValue(
      portal_type="Payment Transaction",
      simulation_state="started",
      causality__uid=context.getUid(),
      payment_mode__uid=[portal.portal_categories.payment_mode.payzen.getUid(),
                         portal.portal_categories.payment_mode.wechat.getUid()],
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
