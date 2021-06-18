from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()
current_invoice = context.getCausalityValue()

if current_invoice is None:
  invoice_template = portal.restrictedTraverse(template)
  current_invoice = invoice_template.Base_createCloneDocument(batch_mode=1)

  subscription_trade_condition = portal.portal_preferences.getPreferredAggregatedSubscriptionSaleTradeCondition()
  user_trade_condition = context.getDestinationSectionValue().\
     Person_getAggregatedSubscriptionSaleTradeConditionValue(subscription_trade_condition)

  if user_trade_condition:
    current_invoice.setSpecialise(user_trade_condition)
  
  context.edit(causality_value=current_invoice)

  payment_transaction = portal.restrictedTraverse(payment)
  current_invoice.edit(
        title="Reservation Fee",
        destination_value=context.getDestinationSection(),
        destination_section_value=context.getDestinationSection(),
        destination_decision_value=context.getDestinationSection(),
        start_date=payment_transaction.getStartDate(),
        stop_date=payment_transaction.getStopDate(),
      )

  if service_variation is not None:
    current_invoice["1"].setVariation(service_variation)
  
  cell = current_invoice["1"]["movement_0"]
  
  cell.edit(
    variation=current_invoice["1"].getVariation(),
    quantity=context.getQuantity()
  )
  cell.setPrice(price)

  # Test to see if the user has specific trade condition for aggregation.
  person = context.getDestinationSectionValue()
  trade_condition = person.Person_getAggregatedSubscriptionSaleTradeConditionValue(
    current_invoice.getSpecialise()
  )
  if trade_condition != current_invoice.getSpecialise():
    current_invoice.edit(specialise=trade_condition)

  comment = "Validation invoice for subscription request %s" % context.getRelativeUrl()
  current_invoice.plan(comment=comment)
  current_invoice.confirm(comment=comment)
  current_invoice.startBuilding(comment=comment)
  payment_transaction.setCausalityValue(current_invoice)
  current_invoice.reindexObject(activate_kw={'tag': tag})

return current_invoice
