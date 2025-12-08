portal = context.getPortalObject()

activate_kw = {'tag': tag, 'priority': 2}
portal.portal_catalog.searchAndActivate(
  portal_type='Support Request',
  simulation_state='suspended',
  method_id='SupportRequest_checkSuspendedToReopen',
  method_kw={'activate_kw': activate_kw},
  activate_kw=activate_kw
)

context.activate(after_tag=tag).getId()
