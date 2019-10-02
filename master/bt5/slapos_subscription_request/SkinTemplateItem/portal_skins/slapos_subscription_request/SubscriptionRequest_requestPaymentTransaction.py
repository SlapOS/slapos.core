from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()

current_invoice = context.getCausalityValue()
current_payment = None

if current_invoice is None:
  # Hardcoded value for reservation
  # currency = context.getSpecialiseValue().getPriceCurrency()
  # XXX: Test for now
  currency = "currency_module/CNY"
  if currency == "currency_module/CNY": # Wechat payment
    payment_template = portal.restrictedTraverse("accounting_module/slapos_wechat_pre_payment_template")
    quantity = int(amount) * 188
  else:
    payment_template = portal.restrictedTraverse("accounting_module/slapos_pre_payment_template")
    quantity = int(amount)*25
  current_payment = payment_template.Base_createCloneDocument(batch_mode=1)

  current_payment.edit(
        title="Payment for Reservation Fee",
        source_value=context.getDestinationSection(),
        destination_value=context.getDestinationSection(),
        destination_section_value=context.getDestinationSection(),
        destination_decision_value=context.getDestinationSection(),
        start_date=DateTime(),
        stop_date=DateTime()
      )


  for line in current_payment.contentValues():
    if line.getSource() == "account_module/bank":
      line.setQuantity(-1*quantity)
    if line.getSource() == "account_module/receivable":
      line.setQuantity(quantity)

  # Accelarate job of alarms before proceed to payment.
  comment = "Validation payment for subscription request %s" % context.getRelativeUrl()
  current_payment.confirm(comment=comment)
  current_payment.start(comment=comment)
  current_payment.PaymentTransaction_updateStatus()
  current_payment.reindexObject(activate_kw={'tag': tag})
  context.reindexObject(activate_kw={'tag': tag})

  context.activate(tag=tag).SubscriptionRequest_createRelatedSaleInvoiceTransaction(
    amount, tag, current_payment.getRelativeUrl())

return current_payment
