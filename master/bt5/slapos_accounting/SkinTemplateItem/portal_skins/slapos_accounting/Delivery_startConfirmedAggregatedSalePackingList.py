from DateTime import DateTime
portal = context.getPortalObject()
if context.getPortalType() != 'Sale Packing List':
  raise TypeError('Incorrect delivery.')
isTransitionPossible = portal.portal_workflow.isTransitionPossible
if context.getSimulationState() == 'confirmed' \
  and len(context.checkConsistency()) == 0 \
  and context.getCausalityState() == 'solved' \
  and context.getSpecialise() in [portal.portal_preferences.getPreferredAggregatedSaleTradeCondition(),
                                  portal.portal_preferences.getPreferredAggregatedSubscriptionSaleTradeCondition()]:

  comment = 'Start by alarm as all actions in confirmed state are ready.'
  date = context.getStartDate()
  if date is None:
    date = DateTime().earliestTime()
  
  context.edit(start_date=date, stop_date=date)
  if isTransitionPossible(context, 'start'):
    context.start(comment=comment)
