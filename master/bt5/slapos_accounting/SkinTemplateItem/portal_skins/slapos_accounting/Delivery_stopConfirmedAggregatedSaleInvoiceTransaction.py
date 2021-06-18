portal = context.getPortalObject()
if context.getPortalType() != 'Sale Invoice Transaction':
  raise TypeError('Incorrect delivery.')
isTransitionPossible = portal.portal_workflow.isTransitionPossible
if context.getSimulationState() == 'confirmed'\
  and len(context.checkConsistency()) == 0\
  and context.getCausalityState() == 'solved'\
  and len(context.objectValues(portal_type="Sale Invoice Transaction Line")):

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
      portal_type="Sale Trade Condition",
      specialise__uid=root_trade_condition_uid_list,
      validation_state="validated")])

    if context.getSpecialiseUid() not in trade_condition_uid_list:
      return

  comment = 'Stopped by alarm as all actions in confirmed state are ready.'
  if isTransitionPossible(context, 'start'):
    context.start(comment=comment)
  if isTransitionPossible(context, 'stop'):
    context.stop(comment=comment)
