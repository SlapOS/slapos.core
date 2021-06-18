from DateTime import DateTime
portal = context.getPortalObject()
if context.getPortalType() != 'Sale Packing List':
  raise TypeError('Incorrect delivery.')
isTransitionPossible = portal.portal_workflow.isTransitionPossible
if context.getSimulationState() == 'started' \
  and len(context.checkConsistency()) == 0 \
  and context.getCausalityState() == 'solved':

  if context.getSpecialise() not in [
      portal.portal_preferences.getPreferredAggregatedSaleTradeCondition(),
      portal.portal_preferences.getPreferredAggregatedSubscriptionSaleTradeCondition()]:
    
    trade_condition_uid_list = []
    # search for user specific trade conditions 
    root_trade_condition_uid_list = [
      portal.restrictedTraverse(
        portal.portal_preferences.getPreferredAggregatedSubscriptionSaleTradeCondition()).getUid(),
      portal.restrictedTraverse(
        portal.portal_preferences.getPreferredAggregatedSaleTradeCondition()).getUid()]

    trade_condition_uid_list.extend(root_trade_condition_uid_list)
    trade_condition_uid_list.extend([
      i.uid for i in portal.portal_catalog(
      specialise__uid=root_trade_condition_uid_list,
      validation_state="validated")])

    if context.getSpecialiseUid() not in trade_condition_uid_list:
      return

  comment = 'Delivered by alarm as all actions in started state are ready.'
  if isTransitionPossible(context, 'stop'):
    context.stop(comment=comment)
  if isTransitionPossible(context, 'deliver'):
    context.deliver(comment=comment)
