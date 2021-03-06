select_kw = kwargs.copy()
select_kw.pop('portal_type', None)
select_kw.pop('delivery_relative_url_list', None)
from Products.ZSQLCatalog.SQLCatalog import Query, NegatedQuery, ComplexQuery
portal = context.getPortalObject()

newTempSimulationMovement = portal.portal_trash.newContent

business_process_uid_list = [
  portal.business_process_module.slapos_reservation_refound_business_process.getUid(),
  portal.business_process_module.slapos_subscription_business_process.getUid()]

specialise_uid_list = [q.getUid() for q in portal.portal_catalog(
  specialise_uid=business_process_uid_list, portal_type='Sale Trade Condition')]

consumption_specialise_uid_list = [q.getUid() for q in portal.portal_catalog(
  specialise_uid=portal.business_process_module.slapos_consumption_business_process.getUid(),
  portal_type='Sale Trade Condition')]

select_dict= {'default_aggregate_portal_type': None}

select_kw.update(
  limit=100, # just take a bit
  portal_type='Sale Packing List Line',
  simulation_state='delivered',
  parent_specialise_uid=specialise_uid_list+consumption_specialise_uid_list,
  select_dict=select_dict,
  left_join_list=select_dict.keys(),
  default_aggregate_portal_type=ComplexQuery(NegatedQuery(Query(default_aggregate_portal_type='Computer')),
    Query(default_aggregate_portal_type=None),logical_operator="OR"),
  grouping_reference=None,
  sort_on=(('modification_date', 'ASC'),) # the highest chance to find movement which can be delivered
)
movement_list = portal.portal_catalog(**select_kw)

specialise = portal.portal_preferences.getPreferredAggregatedSaleTradeCondition()
subscription_request_specialise = portal.portal_preferences.getPreferredAggregatedSubscriptionSaleTradeCondition()
consumption_specialise = portal.portal_preferences.getPreferredAggregatedConsumptionSaleTradeCondition()

if specialise is None:
  raise ValueError("Preferred Aggregated Sale Trade Condition is not Defined, please check your preferences.")

if subscription_request_specialise is None:
  raise ValueError("Preferred Aggregated Subscription Sale Trade Condition is not Defined, please check your preferences.")

if consumption_specialise is None:
  raise ValueError("Preferred Aggregated Consumption Sale Trade Condition is not Defined, please check your preferences.")

temp_movement_list = []
for movement in movement_list:
  if movement.getGroupingReference() is not None:
    continue
  temp_movement = newTempSimulationMovement(
    temp_object=True, id=movement.getRelativeUrl(),
    portal_type="Simulation Movement",
    quantity=movement.getQuantity(),
    resource=movement.getResource(),
    source=movement.getSource(),
    destination=movement.getDestination(),
    source_section=movement.getSourceSection(),
    destination_section=movement.getDestination(),
    destination_decision=movement.getDestination(),
    specialise=specialise,
    price_currency=movement.getPriceCurrency(),
    start_date=movement.getStartDate())

  # XXX Shamefully hardcoded values
  if movement.getResource() == 'service_module/slapos_instance_subscription':
    # reduce tax from there directly
    temp_movement.edit(price=movement.getPrice(0.0)/1.2)
  elif movement.getResource() == 'service_module/slapos_reservation_refund':
    temp_movement.edit(price=movement.getPrice(0.0))
  else:
    temp_movement.edit(price=0.0)

  hosting_subscription = movement.getAggregateValue(portal_type="Hosting Subscription")

  specialise_to_set = subscription_request_specialise
  if movement.getSpecialiseUid() in consumption_specialise_uid_list:
    specialise_to_set = consumption_specialise

  if hosting_subscription is not None:
    subscription = hosting_subscription.getAggregateRelated(portal_type="Subscription Request")
    if subscription is not None:
      temp_movement.edit(
          specialise=specialise_to_set,
          causality=subscription)
  elif movement.getCausality(portal_type="Subscription Request") is not None:
    temp_movement.edit(
      specialise=specialise_to_set,
      causality=movement.getCausality(portal_type="Subscription Request"))

  temp_movement_list.append(temp_movement)

return temp_movement_list
