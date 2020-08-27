from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()

current_invoice = context.getCausalityValue()
current_payment = None

if current_invoice is None:
  if target_language == "zh": # Wechat payment, reservation fee is 188 CNY
    payment_template = portal.restrictedTraverse(portal.portal_preferences.getPreferredZhPrePaymentTemplate())
  else: # Payzen payment, reservation fee is 25 EUR
    payment_template = portal.restrictedTraverse(portal.portal_preferences.getPreferredDefaultPrePaymentTemplate())
  current_payment = payment_template.Base_createCloneDocument(batch_mode=1)

  current_payment.edit(
        title="Payment for Reservation Fee",
        destination_value=context.getDestinationSection(),
        destination_section_value=context.getDestinationSection(),
        destination_decision_value=context.getDestinationSection(),
        start_date=DateTime(),
        stop_date=DateTime()
      )

  if context.SubscriptionRequest_testSkippedReservationFree(contract):
    amount = 0

  for line in current_payment.contentValues():
    if line.getSource() in ["account_module/bank", "account_module/receivable"]:
      quantity = int(amount) * line.getQuantity()
      line.setQuantity(quantity)
   
  # Accelarate job of alarms before proceed to payment.
  comment = "Validation payment for subscription request %s" % context.getRelativeUrl()
  current_payment.confirm(comment=comment)
  current_payment.start(comment=comment)
  current_payment.PaymentTransaction_updateStatus()
  current_payment.reindexObject(activate_kw={'tag': tag})
  context.reindexObject(activate_kw={'tag': tag})

  context.activate(tag=tag).SubscriptionRequest_createRelatedSaleInvoiceTransaction(
    amount, tag, current_payment.getRelativeUrl(), target_language)

return current_payment
