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

  now = DateTime()
  current_payment.edit(
    title="Payment for Reservation Fee",
    specialise_value=trade_condition,
    destination_value=context.getDestinationSection(),
    destination_section_value=context.getDestinationSection(),
    destination_decision_value=context.getDestinationSection(),
    start_date=now,
    stop_date=now,

    payment_mode_uid=payment_mode.getUid(),
    #source_payment_value=trade_condition.getSourcePaymentValue(),
    #source_value=trade_condition.getSourceValue(),
    #source_section_value=trade_condition.getSourceSectionValue(),
    #price_currency_value=trade_condition.getPriceCurrencyValue(),
    #resource=
  )

  current_payment.SaleOrder_applySaleTradeCondition(batch_mode=1, force=1)
  current_payment.edit(
    specialise_value=None,
  )

  # Search for matching resource
  service = portal.portal_catalog(
    # XXX Hardcoded as temporary
    id='slapos_reservation_fee_2',
    portal_type='Service',
    validation_state='validated',
    use__relative_url='use/trade/sale'
  )[0].getObject()

  tmp_invoice_line = portal.accounting_module.newContent(
    temp_object=True,
    portal_type='Sale Invoice Transaction',
    price_currency_value=trade_condition.getPriceCurrencyValue(),
    specialise_value=trade_condition,
  ).newContent(
    temp_object=True,
    portal_type='Invoice Line',
    resource_value=service,
    quantity=context.getQuantity(),
    quantity_unit=service.getQuantityUnit(),
    base_contribution_list=service.getBaseContributionList(),
    use=service.getUse(),
    # price_currency_value=trade_condition.getPriceCurrencyValue()
  )

  # XXX use search predicate list
  price = service.getPrice(
    context=tmp_invoice_line,
    predicate_list=[
      x for x in trade_condition.contentValues(portal_type='Sale Supply Line')
      if x.getResource() == service.getRelativeUrl()
    ]
  )
  # XXX calculate Tax
  # We need to provide Price to pay right the way, so we need to include
  # taxation at this point it is most liketly to quickly forecast price 
  # with taxes, but for now it is hardcoded.
  tax = 0
  if 'base_amount/invoicing/taxable' in tmp_invoice_line.getBaseContributionList():
    for trade_model_line in trade_condition.getAggregatedAmountList(tmp_invoice_line):
      tax = trade_model_line.getPrice()
      # For simplification consider tax is a single value.
      break

  amount = context.getQuantity()
  total = round((int(amount) * price)+(int(amount) * price*tax), 2)

  payable_line = current_payment.newContent(
    portal_type="Accounting Transaction Line",
    quantity=total,
    destination="account_module/payable",
    source="account_module/receivable",
  )
  encash_line = current_payment.newContent(
    portal_type="Accounting Transaction Line",
    quantity=-total,
    # XXX why source/destination are identical?
    destination="account_module/payment_to_encash",
    source="account_module/payment_to_encash",
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

  if not price:
    current_payment.stop(comment="%s (Free)" % comment)
  elif current_payment.getPaymentMode() == "payzen":
    # Payzen require update like this.
    current_payment.PaymentTransaction_updateStatus()

  current_payment.reindexObject(activate_kw={'tag': tag})
  context.reindexObject(activate_kw={'tag': tag})

  context.activate(tag=tag).SubscriptionRequest_createRelatedSaleInvoiceTransaction(
    price, tag, current_payment.getRelativeUrl(), portal.portal_preferences.getPreferredDefaultPrePaymentSubscriptionInvoiceTemplate(),
    service_variation)
return current_payment
