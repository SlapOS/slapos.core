portal = context.getPortalObject()

default_upgrade_scope_uid = [
         portal.portal_categories.upgrade_scope.auto.getUid(),
         portal.portal_categories.upgrade_scope.confirmation.getUid()
    ]

if default_upgrade_scope_uid:
  portal.portal_catalog.searchAndActivate(
    portal_type='Compute Node',
    validation_state = 'validated',
    default_upgrade_scope_uid=default_upgrade_scope_uid,
    method_id = 'ComputeNode_checkAndCreateUpgradeDecision',
    activate_kw = {'tag':tag}
  )

  context.activate(after_tag=tag).getId()
