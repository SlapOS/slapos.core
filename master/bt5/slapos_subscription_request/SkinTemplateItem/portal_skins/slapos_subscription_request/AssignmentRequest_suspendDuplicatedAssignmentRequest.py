from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()
assignment_request = context

workgroup = assignment_request.getDestinationValue(portal_type='Workgroup')
person = assignment_request.getDestinationDecisionValue(portal_type='Person')

if workgroup is None or person is None:
  return

workgroup_assignment_request_list = portal.portal_catalog(
    portal_type='Assignment Request',
    simulation_state='validated',
    destination_decision__uid=workgroup.getUid()
  )

if not len(workgroup_assignment_request_list):
  return

function_map = {}
for assignment_request in workgroup_assignment_request_list:
  function_uid = assignment_request.getFunctionUid()
  if function_uid and assignment_request.getDestinationProject():
    if function_uid in function_map:
      function_map[function_uid].append(assignment_request.getDestinationProjectUid())
    else:
      function_map[function_uid] = [assignment_request.getDestinationProjectUid()]

for function_uid in function_map:
  query_kw = {
    'portal_type': 'Assignment Request',
    'simulation_state': 'validated',
    'destination_project__uid': function_map[function_uid],
    'destination_decision__uid': person.getUid(),
    'function__uid': function_uid
  }
  for assignment_request in portal.portal_catalog(**query_kw):
    assignment_request.suspend(comment='Suspended after join %s' % workgroup.getReference())
