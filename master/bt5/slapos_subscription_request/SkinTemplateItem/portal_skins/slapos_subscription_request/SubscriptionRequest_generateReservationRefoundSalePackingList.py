from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

portal = context.getObject()

if context.REQUEST.get("refund_packing_list_%s" % context.getUid(),
                    None) is not None:
  return

tag = "refund_packing_list_%s_inProfess" % context.getUid()
if (portal.portal_activities.countMessageWithTag(tag) > 0):
  return

service = portal.restrictedTraverse(
    "service_module/slapos_reservation_refund")

if len(portal.portal_catalog(
  default_resource_uid=service.getUid(),
  portal_type="Sale Packing List Line",
  simulation_state="delivered",
  parent_causality_uid=context.getUid())):
  # Already generated
  return

sale_invoice_transaction = context.getCausalityValue(
  portal_type="Sale Invoice Transaction")

if sale_invoice_transaction is None or sale_invoice_transaction.getSimulationState() in ["draft", "cancelled", "deleted"]:
  # No invoice generated, nothing to do
  return

payment_transaction = sale_invoice_transaction.getCausalityRelatedValue(
  portal_type="Payment Transaction")

if payment_transaction is None or payment_transaction.getSimulationState() != "stopped":
  # Nothing to do bug wait the payment
  return

# Time to create the PL
person = sale_invoice_transaction.getDestinationValue(portal_type="Person")
delivery_template = portal.restrictedTraverse(
      portal.portal_preferences.getPreferredInstanceDeliveryTemplate())

delivery = delivery_template.Base_createCloneDocument(batch_mode=1)

delivery.edit(
  title="Reservation Deduction",
  specialise="sale_trade_condition_module/slapos_reservation_refund_trade_condition",
  destination=person.getRelativeUrl(),
  destination_decision=person.getRelativeUrl(),
  start_date=payment_transaction.getCreationDate(),
  causality_uid=context.getUid(),
  price_currency=sale_invoice_transaction.getPriceCurrency()
)

line = delivery.newContent(
      portal_type="Sale Packing List Line",
      title="Reservation Deduction",
      quantity=1,
      destination_value=person,
      destination_decision_value=person,
      destination_section_value=person,
      resource_value=service,
      quantity_unit=service.getQuantityUnit(),
      price=-sale_invoice_transaction.getTotalPrice(),
      causality_uid=context.getUid()
    )

delivery.confirm(comment="Created from %s" % context.getRelativeUrl())
delivery.start()
delivery.stop()
delivery.deliver()
delivery.startBuilding()
delivery.reindexObject(activate_kw={'tag': tag})
line.reindexObject(activate_kw={'tag': tag})


context.REQUEST.set("refound_packing_list_%s" % context.getUid(),
                    delivery)

return delivery
