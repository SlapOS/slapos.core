from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()

current_invoice = context.getCausalityValue()

if current_invoice is None:
  if target_language == "zh": # Wechat payment
    invoice_template_path = portal.portal_preferences.getPreferredZhPrePaymentSubscriptionInvoiceTemplate()
  else:
    invoice_template_path = portal.portal_preferences.getPreferredDefaultPrePaymentSubscriptionInvoiceTemplate()
  invoice_template = portal.restrictedTraverse(invoice_template_path)

  current_invoice = invoice_template.Base_createCloneDocument(batch_mode=1)
  context.edit(causality_value=current_invoice)

  payment_transaction = invoice_template = portal.restrictedTraverse(payment)
  current_invoice.edit(
        title="Reservation Fee",
        source_value=context.getDestinationSection(),
        destination_value=context.getDestinationSection(),
        destination_section_value=context.getDestinationSection(),
        destination_decision_value=context.getDestinationSection(),
        start_date=payment_transaction.getStartDate(),
        stop_date=payment_transaction.getStopDate(),
      )
  current_invoice["1"].setQuantity(amount)

  comment = "Validation invoice for subscription request %s" % context.getRelativeUrl()
  current_invoice.plan(comment=comment)
  current_invoice.confirm(comment=comment)
  current_invoice.startBuilding(comment=comment)
  payment_transaction.setCausalityValue(current_invoice)
  current_invoice.reindexObject(activate_kw={'tag': tag})

return current_invoice
