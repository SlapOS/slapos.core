portal = context.getPortalObject()
portal.portal_catalog.searchAndActivate(
  portal_type="Data Array",
  publication_section_relative_url = 'publication_section/file_system_image/process_state/converted',
  validation_state='validated',
  method_id='DataArray_processDataArray',
  activate_kw={'tag': tag},
)


context.activate(after_tag=tag).getId()
