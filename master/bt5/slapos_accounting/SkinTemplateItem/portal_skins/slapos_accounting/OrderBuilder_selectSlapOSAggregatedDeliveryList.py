# beware: the configuration of OrderBuilder_generateSlapOSAggregatedMovementList shall
# provide small amounts of movements
person_delivery_mapping = {}
portal = context.getPortalObject()

def newPackingList(movement, causality, message):
  delivery = portal.sale_packing_list_module.newContent(
        portal_type='Sale Packing List',
        source=movement.getSource(),
        destination=movement.getDestination(),
        source_section=movement.getSourceSection(),
        destination_section=movement.getDestination(),
        destination_decision=movement.getDestination(),
        specialise=movement.getSpecialise(),
        price_currency=movement.getPriceCurrency(),
        causality=causality,
        start_date=movement.getStartDate())

  delivery.confirm(message)
  return delivery

consumption_specialise_uid_list = [q.getUid() for q in portal.portal_catalog(
  specialise_uid=portal.business_process_module.slapos_consumption_business_process.getUid(),
  portal_type='Sale Trade Condition')]

for movement in movement_list:
  person = movement.getDestinationValue()
  causality = movement.getCausality(portal_type="Subscription Request")
  specialise_uid = movement.getSpecialiseUid()
  try:
    delivery = person_delivery_mapping["%s---%s---%s" % (person.getUid(), causality, specialise_uid)]
    if delivery is None:
      raise KeyError
  except KeyError:
    delivery = person.Person_getAggregatedDelivery()
    if causality is None and (delivery is None or delivery.getSimulationState() != 'confirmed'):
      delivery = newPackingList(movement, causality, 'New aggregated delivery.')
      person.Person_setAggregatedDelivery(delivery)

    elif causality is not None:
      if specialise_uid in consumption_specialise_uid_list:
        subscription_requestion = movement.getCausality(portal_type="Subscription Request")
        delivery = subscription_requestion.SubscriptionRequest_getAggregatedConsumptionDelivery()
        if delivery is None or delivery.getSimulationState() != 'confirmed':
          delivery = newPackingList(movement, causality, 'New aggregated delivery for consumption')
          subscription_requestion.SubscriptionRequest_setAggregatedConsumptionDelivery(delivery)
      else:
        # If causality is not None, this is a delivery from a subscription request, so
        # we create a separated Sale Packing List for it.
        delivery = newPackingList(movement, causality, 'New aggregated delivery for subscription')


    if delivery is not None and delivery.getSource() != movement.getSource():
      delivery.setSource(movement.getSource())
    if delivery is not None and delivery.getSourceSection() != movement.getSourceSection():
      delivery.setSourceSection(movement.getSourceSection())

    person_delivery_mapping["%s---%s---%s" % (person.getUid(), causality, specialise_uid)] = delivery

return person_delivery_mapping.values()
