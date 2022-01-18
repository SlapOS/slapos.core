from DateTime import DateTime
portal = context.getPortalObject()
if context.getPortalType() != 'Sale Packing List':
  raise TypeError('Incorrect delivery.')



isTransitionPossible = portal.portal_workflow.isTransitionPossible
if context.getSimulationState() == 'confirmed' \
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
      i.uid for i in portal.ERP5Site_searchRelatedInheritedSpecialiseList(
      specialise_uid=root_trade_condition_uid_list,
      validation_state="validated")])

    if context.getSpecialiseUid() not in trade_condition_uid_list:
      return

  comment = 'Start by alarm as all actions in confirmed state are ready.'
  date = context.getStartDate()
  if date is None:
    date = DateTime().earliestTime()
  
  context.edit(start_date=date, stop_date=date)
  if isTransitionPossible(context, 'start'):
    context.start(comment=comment)
