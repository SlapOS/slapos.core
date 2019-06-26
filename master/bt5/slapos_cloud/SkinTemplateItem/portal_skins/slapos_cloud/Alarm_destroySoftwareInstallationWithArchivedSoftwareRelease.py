portal = context.getPortalObject()

portal.portal_catalog.searchAndActivate(
  portal_type='Software Installation',
  validation_state = 'validated',
  method_id = 'SoftwareInstallation_destroyWithSoftwareReleaseArchived',
  activate_kw = {'tag':tag}
)

context.activate(after_tag=tag).getId()
