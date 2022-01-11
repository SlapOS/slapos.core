portal = context.getPortalObject()
from DateTime import DateTime

if context.getPortalType() != 'Sale Invoice Transaction':
  raise TypeError('Incorrect delivery.')

now = DateTime()
isTransitionPossible = portal.portal_workflow.isTransitionPossible
if (context.getSimulationState() == 'confirmed')\
  and (context.getLedger() == 'automated')\
  and (context.getCausalityState() == 'solved')\
  and (0 < len(context.objectValues(portal_type="Sale Invoice Transaction Line"))\
  and (context.getStopDate(now) <= now)):

  if context.getSourcePayment("") == "":
    context.setSourcePayment(context.AccountingTransaction_getSourcePaymentItemList()[-1][1])

  assert context.getSourcePayment("") != ""

  if (len(context.checkConsistency()) == 0):
    comment = 'Stopped by alarm as all actions in confirmed state are ready.'
    if isTransitionPossible(context, 'start'):
      context.start(comment=comment)
    if isTransitionPossible(context, 'stop'):
      context.stop(comment=comment)
