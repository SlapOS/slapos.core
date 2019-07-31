portal = context.getPortalObject()

portal.portal_catalog.searchAndActivate(
  portal_type='Slave Instance',
  validation_state = 'validated',
  method_id = 'SlaveInstance_automaticallyUpgradeHostingSubscription',
  method_kw = {'tag': tag},
  activate_kw = {'tag':tag}
)

context.activate(after_tag=tag).getId()
