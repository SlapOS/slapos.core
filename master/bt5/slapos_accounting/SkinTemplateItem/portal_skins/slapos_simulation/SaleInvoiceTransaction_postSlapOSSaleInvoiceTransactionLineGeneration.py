from Products.ERP5Type.Message import translateString

comment = translateString('Initialised by Delivery Builder.')
isTransitionPossible = context.getPortalObject().portal_workflow.isTransitionPossible

if isTransitionPossible(context, 'startBuilding'):
  context.startBuilding(comment=comment)
