portal = context.getPortalObject()
Base_translateString = portal.Base_translateString

upgrade_decision = context.InstanceTree_createUpgradeDecision(
  target_software_release=target_software_release,
  target_software_type=context.getSourceReference()
)

if upgrade_decision is None:
  return context.Base_renderForm(dialog_id, Base_translateString('Can not propose an upgrade to this release'), level='error')
else:
  return upgrade_decision.Base_redirect()
