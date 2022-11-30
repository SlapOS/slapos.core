from DateTime import DateTime


portal = context.getPortalObject()
portal_membership=portal.portal_membership

demo_user_functional = portal_membership.getAuthenticatedMember().getUserValue()


def wrapWithShadow():
  payment_template = portal.restrictedTraverse(portal.portal_preferences.getPreferredDefaultPrePaymentTemplate())
  payment = payment_template.Base_createCloneDocument(batch_mode=1)

  for line in payment.contentValues():
    if line.getSource() == "account_module/payment_to_encash":
      line.setQuantity(-1)
    elif line.getSource() == "account_module/receivable":
      line.setQuantity(1)

  payment.confirm()
  payment.start()
  if not unpaid:
    payment.stop()
    payment.PaymentTransaction_generatePayzenId()

  template = portal.restrictedTraverse(portal.portal_preferences.getPreferredDefaultPrePaymentSubscriptionInvoiceTemplate())
  current_invoice = template.Base_createCloneDocument(batch_mode=1)

  current_invoice.edit(
        destination_value=demo_user_functional,
        destination_section_value=demo_user_functional,
        destination_decision_value=demo_user_functional,
        start_date=DateTime('2019/10/20'),
        stop_date=DateTime('2019/10/20'),
        title='Fake Invoice for Demo User Functional',
        price_currency="currency_module/EUR",
        reference='1')

  cell = current_invoice["1"]["movement_0"]
  
  cell.edit(
    quantity=1
  )
  cell.setPrice(1)
  return current_invoice, payment

current_invoice, payment = demo_user_functional.Person_restrictMethodAsShadowUser(
  shadow_document=demo_user_functional,
  callable_object=wrapWithShadow,
  argument_list=[])

payment.setCausalityValue(current_invoice)
payment.setDestinationSectionValue(demo_user_functional)

current_invoice.plan()
current_invoice.confirm()
current_invoice.startBuilding()
current_invoice.reindexObject()
current_invoice.stop()

current_invoice.activate(after_method_id="immediateReindexObject").Delivery_manageBuildingCalculatingDelivery()

current_invoice.activate(
  after_method_id=(
    "immediateReindexObject", "_updateSimulation", "Delivery_manageBuildingCalculatingDelivery")
  ).SaleInvoiceTransaction_forceBuildSlapOSAccountingLineList()

if not unpaid:
  current_invoice.activate(
  after_method_id=(
    "immediateReindexObject",
    "_updateSimulation",
    "Delivery_manageBuildingCalculatingDelivery",
    "SimulationMovement_buildSlapOS",
    "SaleInvoiceTransaction_forceBuildSlapOSAccountingLineList")
  ).SaleInvoiceTransaction_setFakeGroupingReference()
  payment.activate(
    after_method_id=(
      "immediateReindexObject",
      "_updateSimulation",
      "Delivery_manageBuildingCalculatingDelivery",
      "SimulationMovement_buildSlapOS",
      "SaleInvoiceTransaction_forceBuildSlapOSAccountingLineList")
    ).SaleInvoiceTransaction_setFakeGroupingReference()

return 'Done.'
