from Products.ERP5Type.Message import translateString

upgrade_decision = context
portal = context.getPortalObject()

if portal.portal_workflow.isTransitionPossible(upgrade_decision, 'reject'):
  upgrade_decision.reject()

if not batch:
  return upgrade_decision.Base_redirect(
    keep_items={'portal_status_message': translateString('Upgrade Decision rejected.')}
  )
