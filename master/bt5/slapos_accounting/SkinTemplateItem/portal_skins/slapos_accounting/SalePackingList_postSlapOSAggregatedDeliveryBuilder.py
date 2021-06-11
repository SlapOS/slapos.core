from DateTime import DateTime
portal = context.getPortalObject()
restrictedTraverse = portal.restrictedTraverse

person = context.getDestination()
reference = context.getReference()

business_process_uid_list = [
  portal.business_process_module.slapos_reservation_refound_business_process.getUid(),
  portal.business_process_module.slapos_subscription_business_process.getUid()]

specialise_list = [q.getRelativeUrl() for q in portal.portal_catalog(
  specialise_uid=business_process_uid_list, portal_type='Sale Trade Condition')]

consumption_specialise_list = [q.getRelativeUrl() for q in portal.portal_catalog(
  specialise_uid=portal.business_process_module.slapos_consumption_business_process.getUid(),
  portal_type='Sale Trade Condition')]

subscription_request_specialise = portal.portal_preferences.getPreferredAggregatedSubscriptionSaleTradeCondition()
consumption_specialise = portal.portal_preferences.getPreferredAggregatedConsumptionSaleTradeCondition()

trade_condition = context.getSpecialise()

specialise_filter_list = consumption_specialise_list + specialise_list
if trade_condition == consumption_specialise:
  specialise_filter_list = consumption_specialise_list
elif trade_condition == subscription_request_specialise:
  specialise_filter_list = specialise_list

def test_for_subscription(movement, causality):
  instance_tree = movement.getAggregateValue(portal_type="Instance Tree")
  if instance_tree is not None:
    return instance_tree.getAggregateRelated(portal_type="Subscription Request") == causality

  if movement.getCausality(portal_type="Subscription Request") is not None:
    return movement.getCausality(portal_type="Subscription Request") == causality
  
  return movement.getCausality() == causality

causality = context.getCausality(portal_type="Subscription Request")
input_movement_list = [restrictedTraverse(q) for q in
    related_simulation_movement_path_list
    if restrictedTraverse(q).getDestination() == person and \
      restrictedTraverse(q).getSpecialise() in specialise_filter_list and \
      test_for_subscription(restrictedTraverse(q), causality)]

min_start_date = None
for delivery_line in input_movement_list:
  delivery_line.setGroupingReference(reference)

  if min_start_date is None:
    min_start_date = delivery_line.getStartDate()
  elif delivery_line.getStartDate() < min_start_date:
    min_start_date = delivery_line.getStartDate()

if context.getCausalityState() == 'draft':
  context.startBuilding()

if context.getStartDate() is None:
  if min_start_date is None:
    min_start_date = DateTime().earliestTime()
  context.setStartDate(min_start_date)
