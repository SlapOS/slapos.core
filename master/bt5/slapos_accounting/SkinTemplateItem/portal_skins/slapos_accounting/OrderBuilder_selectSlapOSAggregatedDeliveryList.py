# beware: the configuration of OrderBuilder_generateSlapOSAggregatedMovementList shall
# provide small amounts of movements
person_delivery_mapping = {}
portal = context.getPortalObject()

def newPackingList(movement, causality):
  return portal.sale_packing_list_module.newContent(
        portal_type='Sale Packing List',
        source=movement.getDestination(),
        destination=movement.getDestination(),
        source_section=movement.getSourceSection(),
        destination_section=movement.getDestination(),
        destination_decision=movement.getDestination(),
        specialise=movement.getSpecialise(),
        price_currency=movement.getPriceCurrency(),
        causality=causality)

for movement in movement_list:
  person = movement.getDestinationValue()
  causality = movement.getCausality(portal_type="Subscription Request")
  try:
    delivery = person_delivery_mapping["%s---%s" % (person.getUid(), causality)]
  except KeyError:
    delivery = person.Person_getAggregatedDelivery()
    if causality is None and (delivery is None or delivery.getSimulationState() != 'confirmed'):
      delivery = newPackingList(movement, causality)
      delivery.confirm('New aggregated delivery.')
      person.Person_setAggregatedDelivery(delivery)
    elif causality is not None:
      # If causality is not None, this is a delivery from a subscription request, so
      # we create a separated Sale Packing List for it.
      delivery = newPackingList(movement, causality)
      delivery.confirm('New aggregated delivery for subscription')

    person_delivery_mapping["%s---%s" % (person.getUid(), causality)] = delivery
return person_delivery_mapping.values()
