from DateTime import DateTime

portal = context.getPortalObject()

portal.portal_catalog.searchAndActivate(
  portal_type="Data Array",
  publication_section_relative_url="publication_section/file_system_image/node_image",
  validation_state="draft",
  method_id='DataArray_generateDiffND',
  activate_kw={'tag': tag},
)


context.activate(after_tag=tag).getId()
