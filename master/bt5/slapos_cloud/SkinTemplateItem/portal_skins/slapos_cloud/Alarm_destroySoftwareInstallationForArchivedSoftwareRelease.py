portal = context.getPortalObject()

active_process = context.newActiveProcess()

portal.portal_catalog.searchAndActivate(
  portal_type='Software Release',
  validation_state = 'archived',
  method_id = 'SoftwareRelease_destroyNotUsedSoftwareInstallation',
  method_kw = {'active_process': active_process.getRelativeUrl()},
  activate_kw = {'tag':tag}
)

context.activate(after_tag=tag).getId()
