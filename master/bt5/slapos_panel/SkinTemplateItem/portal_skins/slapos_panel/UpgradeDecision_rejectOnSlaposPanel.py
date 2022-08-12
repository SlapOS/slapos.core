from Products.ERP5Type.Message import translateString

upgrade_decision = context

upgrade_decision.reject()

return upgrade_decision.Base_redirect(
  keep_items={'portal_status_message': translateString('Upgrade Decision rejected.')}
)
