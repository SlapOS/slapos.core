portal = context.getPortalObject()

activate_kw = {'tag': tag}

portal.portal_catalog.searchAndActivate(
  portal_type='Assignment Request',
  simulation_state='validated',
  destination__portal_type='Workgroup',
  destination_decision__portal_type='Person',
  method_id='AssignmentRequest_claimSubscriptionRequestToWorkgroup',
  method_kw={'activate_kw': activate_kw},
  activate_kw=activate_kw
)

context.activate(after_tag=tag).getId()
