if context.getValidationState() != 'archived':
  return
portal = context.getPortalObject()

catalog_kw = dict(
  portal_type='Software Installation',
  validation_state='validated',
  url_string=context.getUrlString(),
  **{"slapos_item.slap_state": "start_requested"}
)

portal.portal_catalog.searchAndActivate(
  method_id = 'SoftwareInstallation_destroyWithSoftwareReleaseArchived',
  activate_kw = {'tag':tag},
  **catalog_kw
)
