portal = context.getPortalObject()

default_allocation_scope_uid = [category.getUid() \
         for category in portal.portal_categories.allocation_scope.open.objectValues()]


if default_allocation_scope_uid:
  portal.portal_catalog.searchAndActivate(
    portal_type='Computer',
    validation_state = 'validated',
    default_allocation_scope_uid=default_allocation_scope_uid,
    method_id = 'Computer_checkAndCreateUpgradeDecision',
    activate_kw = {'tag':tag}
  )

  context.activate(after_tag=tag).getId()
