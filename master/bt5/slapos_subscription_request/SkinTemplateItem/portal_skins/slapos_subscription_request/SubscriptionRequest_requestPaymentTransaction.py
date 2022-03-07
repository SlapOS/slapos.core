from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()

current_invoice = context.getCausalityValue()
current_payment = None
service_variation = None

if current_invoice is None:
  target_language = context.getLanguage()
  """
  if target_language == "zh": # Wechat payment, reservation fee is 188 CNY
    payment_template = portal.restrictedTraverse(portal.portal_preferences.getPreferredZhPrePaymentTemplate())
    invoice_template = portal.restrictedTraverse(portal.portal_preferences.getPreferredZhPrePaymentSubscriptionInvoiceTemplate())
  else: # Payzen payment, reservation fee is 25 EUR
    payment_template = portal.restrictedTraverse(portal.portal_preferences.getPreferredDefaultPrePaymentTemplate())
    invoice_template = portal.restrictedTraverse(portal.portal_preferences.getPreferredDefaultPrePaymentSubscriptionInvoiceTemplate())
  """

  # PaymentTransaction_init is guarded by the owner role
  # but SubscriptionRequest_requestPaymentTransaction is called with a shadow user
  # leading to unauthorized error
  # Instead, clone one temp payment (as there is no PaymentTransaction_afterClone)
  payment_template = portal.restrictedTraverse(portal.portal_preferences.getPreferredDefaultPrePaymentTemplate())
  current_payment = payment_template.Base_createCloneDocument(batch_mode=1)
  assert current_payment is not None
  current_payment.manage_delObjects([x for x in
                                     current_payment.contentIds()])
  current_payment.edit(
    categories=[],
    title=None
  )

  subscription_condition = context.getSpecialiseValue(portal_type='Subscription Condition')
  trade_condition = subscription_condition.getSpecialiseValue(portal_type='Sale Trade Condition')
  assert trade_condition is not None
  # XXX if we have a tree of trade condition, getPaymentMode may be empty (if there is no acquisition)
  payment_mode = trade_condition.getPaymentModeValue()

  current_payment.edit(
    title="Payment for Reservation Fee",
    destination_value=context.getDestinationSection(),
    destination_section_value=context.getDestinationSection(),
    destination_decision_value=context.getDestinationSection(),
    start_date=DateTime(),
    stop_date=DateTime(),
    payment_mode_uid=payment_mode.getUid()
  )

  """
  amount = context.getQuantity()
  if 0:#context.SubscriptionRequest_testSkippedReservationFree(contract):
    # Reservation is Free
    price = 0
    tax = 0
  # else:
  elif 0:
    invoice_line = invoice_template["1"].asContext(
      destination_section=context.getDestinationSection(),
      start_date=DateTime(),
      stop_date=DateTime()
    )

    subscription_trade_condition = portal.portal_preferences.getPreferredAggregatedSubscriptionSaleTradeCondition()
    # XXX drop using Person_getAggregatedSubscriptionSaleTradeConditionValue
    # Instead, put the info on the selected trade condition
    # If user need a specific one, he must select it explicitely
    raise NotImplementedError('couscous')
    user_trade_condition = context.getDestinationSectionValue().\
       Person_getAggregatedSubscriptionSaleTradeConditionValue(subscription_trade_condition)

    if user_trade_condition:
      invoice_line.edit(
        specialise=user_trade_condition,
        destination_section=context.getDestinationSection())
  
    resource = invoice_line.getResourceValue()
    if variation_reference is not None:
      for variation in resource.objectValues(portal_type="Service Individual Variation"):
        if variation.getReference() == variation_reference:
          service_variation = variation.getRelativeUrl()
          invoice_line.setVariation(service_variation)

    price = invoice_line.getResourceValue().getPrice(
                          context=invoice_line)
    
    # We need to provide Price to pay right the way, so we need to include
    # taxation at this point it is most liketly to quickly forecast price 
    # with taxes, but for now it is hardcoded.
    tax = 0
    if 'base_amount/invoicing/taxable' in invoice_line.getBaseContributionList():
      specialise = invoice_line.getSpecialiseValue(portal_type='Sale Trade Condition')
      if specialise is not None:
        for trade_model_line in specialise.getAggregatedAmountList(invoice_line):
          tax = trade_model_line.getPrice()
          # For simplification consider tax is a single value.
          break

  for line in current_payment.contentValues():
    if line.getSource() == "account_module/payment_to_encash":
      total = round((-int(amount) * price)+(-int(amount) * price*tax), 2)
      line.setQuantity(total)
    elif line.getSource() == "account_module/receivable":
      total = round((int(amount) * price)+(int(amount) * price*tax), 2)
      line.setQuantity(total)
"""
  # Accelarate job of alarms before proceed to payment.
  comment = "Validation payment for subscription request %s" % context.getRelativeUrl()
  current_payment.confirm(comment=comment)
  current_payment.start(comment=comment)
  """
  if not price:
    current_payment.stop(comment="%s (Free)" % comment)
  elif target_language != "zh":
    # Payzen don't require update like this.
    current_payment.PaymentTransaction_updateStatus()
"""
  current_payment.reindexObject(activate_kw={'tag': tag})
  context.reindexObject(activate_kw={'tag': tag})

  context.activate(tag=tag).SubscriptionRequest_createRelatedSaleInvoiceTransaction(
    -1, tag, current_payment.getRelativeUrl(), portal.portal_preferences.getPreferredDefaultPrePaymentSubscriptionInvoiceTemplate(),
    service_variation)
return current_payment
