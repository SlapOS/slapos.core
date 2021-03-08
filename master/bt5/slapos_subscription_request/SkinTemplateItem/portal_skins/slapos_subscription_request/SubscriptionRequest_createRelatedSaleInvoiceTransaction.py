from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()
current_invoice = context.getCausalityValue()

if current_invoice is None:
  invoice_template = portal.restrictedTraverse(template)
  current_invoice = invoice_template.Base_createCloneDocument(batch_mode=1)
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

  current_invoice["1"].setPrice(price)
  current_invoice["1"].setQuantity(context.getQuantity())

  comment = "Validation invoice for subscription request %s" % context.getRelativeUrl()
  current_invoice.plan(comment=comment)
  current_invoice.confirm(comment=comment)
  current_invoice.startBuilding(comment=comment)
  payment_transaction.setCausalityValue(current_invoice)
  current_invoice.reindexObject(activate_kw={'tag': tag})

return current_invoice
