if context.getValidationState() != 'archived':
  return
portal = context.getPortalObject()

catalog_kw = dict(
  portal_type='Software Installation',
  validation_state='validated',
  url_string=context.getUrlString()
)

count = portal.portal_catalog.countResults(
  **catalog_kw
)

if count[0][0] == 0:
  context.cleanup(comment='No more validated Software Installations found')
else:
  portal.portal_catalog.searchAndActivate(
    method_id = 'SoftwareInstallation_destroyWithSoftwareReleaseArchived',
    activate_kw = {'tag':tag},
    **catalog_kw
  )
