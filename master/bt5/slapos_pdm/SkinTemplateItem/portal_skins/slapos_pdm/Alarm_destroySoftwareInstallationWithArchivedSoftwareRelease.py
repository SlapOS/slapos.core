portal = context.getPortalObject()

portal.portal_catalog.searchAndActivate(
  portal_type='Software Release',
  validation_state = 'archived',
  method_id = 'SoftwareRelease_findAndDestroySoftwareInstallation',
  method_kw = {'tag': tag},
  activate_kw = {'tag':tag}
)

context.activate(after_tag=tag).getId()
