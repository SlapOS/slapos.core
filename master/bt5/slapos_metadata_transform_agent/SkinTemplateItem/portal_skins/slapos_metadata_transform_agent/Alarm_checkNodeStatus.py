from DateTime import DateTime

portal = context.getPortalObject()

portal.portal_catalog.searchAndActivate(
  portal_type="Data Array",
  simulation_state="converted",
  method_id='DataArray_generateDiffND',
  activate_kw={'tag': tag},
)


context.activate(after_tag=tag).getId()
