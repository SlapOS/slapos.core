portal = context.getPortalObject()
portal_type = context.getDeliveryPortalType()
simulation_state = 'confirmed'

# use catalog to prefetch, but check later in ZODB
return [x.getObject() for x in portal.portal_catalog(
   portal_type=portal_type,
   ledger__uid=portal.portal_categories.ledger.automated.getUid(),
   specialise__uid=list(set([x.getSpecialiseUid() for x in movement_list])),
   destination_section__uid=list(set([x.getDestinationSectionUid() for x in movement_list])),
   simulation_state=simulation_state) if x.getSimulationState() == simulation_state]
