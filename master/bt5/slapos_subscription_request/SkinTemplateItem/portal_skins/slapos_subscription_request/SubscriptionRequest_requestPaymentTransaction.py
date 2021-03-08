from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()

current_invoice = context.getCausalityValue()
current_payment = None

if current_invoice is None:
  if target_language == "zh": # Wechat payment, reservation fee is 188 CNY
    payment_template = portal.restrictedTraverse(portal.portal_preferences.getPreferredZhPrePaymentTemplate())
    invoice_template = portal.restrictedTraverse(portal.portal_preferences.getPreferredZhPrePaymentSubscriptionInvoiceTemplate())
  else: # Payzen payment, reservation fee is 25 EUR
    payment_template = portal.restrictedTraverse(portal.portal_preferences.getPreferredDefaultPrePaymentTemplate())
    invoice_template = portal.restrictedTraverse(portal.portal_preferences.getPreferredDefaultPrePaymentSubscriptionInvoiceTemplate())

  current_payment = payment_template.Base_createCloneDocument(batch_mode=1)
  current_payment.edit(
        title="Payment for Reservation Fee",
        destination_value=context.getDestinationSection(),
        destination_section_value=context.getDestinationSection(),
        destination_decision_value=context.getDestinationSection(),
        start_date=DateTime(),
        stop_date=DateTime()
      )

  amount = context.getQuantity()
  if context.SubscriptionRequest_testSkippedReservationFree(contract):
    # Reservation is Free
    price = 0
    tax = 0
  else:
    invoice_line = invoice_template["1"].asContext()
    price = invoice_line.getResourceValue().getPrice(
                          context=invoice_line)
    
    # We need to provide Price to pay right the way, so we need to include
    # taxation at this point it is most liketly to quickly forecast price 
    # with taxes, but for now it is hardcoded.
    tax = 0
    if 'base_amount/invoicing/taxable' in invoice_line.getBaseContributionList():
      tax = 0.2


  for line in current_payment.contentValues():
    if line.getSource() == "account_module/payment_to_encash":
      total = round((-int(amount) * price)+(-int(amount) * price*tax), 2)
      line.setQuantity(total)
    elif line.getSource() == "account_module/receivable":
      total = round((int(amount) * price)+(int(amount) * price*tax), 2)
      line.setQuantity(total)
   
  # Accelarate job of alarms before proceed to payment.
  comment = "Validation payment for subscription request %s" % context.getRelativeUrl()
  current_payment.confirm(comment=comment)
  current_payment.start(comment=comment)
  if not amount:
    current_payment.stop(comment="%s (Free)" % comment)
  elif target_language != "zh":
    # Payzen don't require update like this.
    current_payment.PaymentTransaction_updateStatus()
  current_payment.reindexObject(activate_kw={'tag': tag})
  context.reindexObject(activate_kw={'tag': tag})

  context.activate(tag=tag).SubscriptionRequest_createRelatedSaleInvoiceTransaction(
    price, tag, current_payment.getRelativeUrl(), invoice_template.getRelativeUrl())

return current_payment
