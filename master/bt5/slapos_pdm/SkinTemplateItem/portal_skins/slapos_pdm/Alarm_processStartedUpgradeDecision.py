portal = context.getPortalObject()
portal.portal_catalog.searchAndActivate(
  portal_type='Upgrade Decision',
  simulation_state='started',
  method_id='requestUpgrade',
  activate_kw={'tag': tag }
)

context.activate(after_tag=tag).getId()
