from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()
current_invoice = context.getCausalityValue()

if current_invoice is None:
  # _init is guarded by the owner role
  # but SubscriptionRequest_createRelatedSaleInvoiceTransaction is called with a shadow user
  # leading to unauthorized error
  # Instead, clone one temp invoice (as there is no _afterClone)
  invoice_template = portal.restrictedTraverse(template)
  current_invoice = invoice_template.Base_createCloneDocument(batch_mode=1)
  assert current_invoice is not None
  current_invoice.manage_delObjects([x for x in
                                     current_invoice.contentIds() if x != "1"])
  current_invoice.edit(
    categories=[],
    title=None
  )
  current_invoice["1"].manage_delObjects([x for x in
                                          current_invoice["1"].contentIds()])
  current_invoice["1"].edit(
    categories=[],
    title=None,
    quantity=None,
    price=None,
    base_unit_price=None,
    #index=None,
    #variation_base_category_list=None,
    #variation_category_list=None,
  )
  current_invoice["1"].updateCellRange('movement')

  context.edit(causality_value=current_invoice)

  payment_transaction = portal.restrictedTraverse(payment)
  current_invoice.edit(
    title="Reservation Fee",
    destination_value=context.getDestinationSection(),
    destination_section_value=context.getDestinationSection(),
    destination_decision_value=context.getDestinationSection(),
    start_date=payment_transaction.getStartDate(),
    stop_date=payment_transaction.getStopDate(),

    specialise=portal.portal_preferences.getPreferredAggregatedSubscriptionSaleTradeCondition(),

    source_section_value=payment_transaction.getSourceSectionValue(),
    source_value=payment_transaction.getSourceValue(),
    payment_mode_value=payment_transaction.getPaymentModeValue(),
    price_currency_value=payment_transaction.getPriceCurrencyValue(),
    resource_value=payment_transaction.getResourceValue(),
  )

  current_invoice["1"].edit(
    start_date=payment_transaction.getStartDate(),
    stop_date=payment_transaction.getStopDate(),

    use="trade/sale",
    resource="service_module/slapos_reservation_fee_2",
    quantity_unit="unit/piece",
    base_contribution_list=[
      "base_amount/invoicing/discounted",
      "base_amount/invoicing/taxable"
    ],
    quantity=context.getQuantity(),
    price=price
  )

  comment = "Validation invoice for subscription request %s" % context.getRelativeUrl()
  current_invoice.plan(comment=comment)
  current_invoice.confirm(comment=comment)
  current_invoice.startBuilding(comment=comment)
  payment_transaction.setCausalityValue(current_invoice)
  current_invoice.reindexObject(activate_kw={'tag': tag})

return current_invoice
