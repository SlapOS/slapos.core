from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()
document = context
assert order_movement.isTempObject()
assert order_movement.getPortalType() == "Sale Order"

consumption_delivery = portal.consumption_delivery_module.newContent(
  portal_type="Consumption Delivery",
  title=title,
  source_value=order_movement.getSourceValue(),
  source_section_value=order_movement.getSourceSectionValue(),
  source_decision_value=order_movement.getSourceDecisionValue(),
  destination_value=order_movement.getDestinationValue(),
  destination_section_value=order_movement.getDestinationSectionValue(),
  destination_decision_value=order_movement.getDestinationDecisionValue(),
  price_currency_value=order_movement.getPriceCurrencyValue(),
  specialise_value=order_movement.getSpecialiseValue(),
  ledger_value=order_movement.getLedgerValue(),
  causality_value=document,
  start_date=start_date,
  stop_date=stop_date,

  # Copy original dates here
  effective_date=start_date,
  expiration_date=stop_date
)

if context.getPortalType() != 'Project':
  # The movements created for Virtual Master dont carry source project
  # because Resource_createSubscriptionRequest don't set it.
  consumption_delivery.edit(
    source_project_value=order_movement.getSourceProjectValue(),
    destination_project_value=order_movement.getDestinationProjectValue()
  )

for line in order_movement.contentValues(portal_type="Sale Order Line"):
  consumption_line = consumption_delivery.newContent(
    portal_type="Consumption Delivery Line",
    title=line.getTitle(),
    quantity=line.getQuantity(),
    aggregate_value=line.getAggregateValueList(),
    resource_value=line.getResourceValue(),
    quantity_unit=line.getQuantityUnit(),
    base_contribution_list=line.getBaseContributionList(),
    use_list=line.getUseList()
  )
  consumption_line.setPrice(line.getPrice(None))

consumption_delivery.Delivery_fixBaseContributionTaxableRate()
consumption_delivery.Base_checkConsistency()
consumption_delivery.confirm(comment="Created from %s" % context.getRelativeUrl())
consumption_delivery.start()
consumption_delivery.stop()
consumption_delivery.deliver()
consumption_delivery.startBuilding()

return consumption_delivery
