portal = context.getPortalObject()

activate_kw = {'tag': tag}
portal.portal_catalog.searchAndActivate(
  portal_type=portal.getPortalEventTypeList(),
  simulation_state='stopped',
  follow_up__portal_type='Support Request',
  method_id='Event_checkStoppedFromSupportRequestToDeliver',
  method_kw={'activate_kw': activate_kw},
  activate_kw=activate_kw
)

context.activate(after_tag=tag).getId()
