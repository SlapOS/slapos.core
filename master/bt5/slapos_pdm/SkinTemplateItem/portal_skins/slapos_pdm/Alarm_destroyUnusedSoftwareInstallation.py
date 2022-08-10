portal = context.getPortalObject()

portal.portal_catalog.searchAndActivate(
  method_id = 'SoftwareInstallation_destroyIfUnused',
  activate_kw = {'tag':tag},
  portal_type='Software Installation',
  validation_state='validated',
  **{"slapos_item.slap_state": "start_requested"}
)

context.activate(after_tag=tag).getId()
