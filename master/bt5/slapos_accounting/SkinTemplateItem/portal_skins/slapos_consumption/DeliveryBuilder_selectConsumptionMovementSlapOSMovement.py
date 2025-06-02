select_dict= {'delivery_uid': None}
kw['select_dict']=select_dict
kw['left_join_list']=select_dict.keys()
kw['delivery_uid']=None
kw['group_by']=('uid',)

portal = context.getPortalObject()
ledger_uid = portal.portal_categories.ledger.automated.getUid()
kw['ledger__uid'] = ledger_uid
kw['strict_use_uid'] = portal.portal_categories.use.trade.consumption.getUid()

movement_list = portal.portal_catalog(**kw)
if not len(movement_list):
  return movement_list

simulation_state = 'confirmed'
# Ensure to only continue if there are some deliveries to merge
# use catalog to prefetch, but check later in ZODB
delivery_list = [x.getObject() for x in portal.portal_catalog(
   portal_type=context.getDeliveryPortalType(),
   ledger__uid=ledger_uid,
   specialise__uid=list(set([x.getSpecialiseUid() for x in movement_list])),
   destination_section__uid=list(set([x.getDestinationSectionUid() for x in movement_list])),
   simulation_state=simulation_state) if x.getSimulationState() == simulation_state]

if len(delivery_list):
  return movement_list
return []
