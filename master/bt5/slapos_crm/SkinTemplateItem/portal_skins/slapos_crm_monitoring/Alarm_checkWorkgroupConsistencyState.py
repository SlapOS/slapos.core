portal = context.getPortalObject()
activate_kw = {'tag': tag, 'priority': 5}

# Search user assignment to automatically close:
# - customer without own instance
# - manager without owning the project
portal.portal_catalog.searchAndActivate(
  portal_type='Assignment Request',
  simulation_state='validated',
  destination__portal_type='Workgroup',
  destination_decision__portal_type='Person',

  method_id='AssignmentRequest_suspendIfDuplicatedByWorkgroup',
  method_kw={'activate_kw': activate_kw},
  activate_kw=activate_kw
)

# Search person which are customer of the same project from multiple conflicting assignments
portal.portal_catalog.searchAndActivate(
  portal_type='Assignment Request',
  simulation_state='validated',
  destination__portal_type='Workgroup',
  destination_decision__portal_type='Person',

  group_by=['destination_decision_uid'],

  method_id='AssignmentRequest_checkPersonWorkgroupConsistency',
  method_kw={'activate_kw': activate_kw},
  activate_kw=activate_kw
)

context.activate(after_tag=tag).getId()
