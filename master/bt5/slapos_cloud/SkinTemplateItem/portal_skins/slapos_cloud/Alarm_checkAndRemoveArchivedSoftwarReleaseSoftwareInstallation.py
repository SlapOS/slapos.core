portal = context.getPortalObject()
portal.portal_catalog.searchAndActivate(
  portal_type='Software Release',
  validation_state = 'archived',
  method_id = 'SoftwareRelease_removeNotUsedSoftwareInstallation',
  #packet_size=1,
  activate_kw = {'tag':tag}
)

context.activate(after_tag=tag).getId()
