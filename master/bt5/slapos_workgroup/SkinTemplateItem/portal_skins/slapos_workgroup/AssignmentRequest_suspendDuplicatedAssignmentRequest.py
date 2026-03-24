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
    destination_decision__uid=workgroup.getUid(),
    function__uid=portal.portal_categories.function.production.customer.getUid()
  )

if not len(workgroup_assignment_request_list):
  return

project_uid_list = [
  x.getDestinationProjectUid() for x in workgroup_assignment_request_list
    if x.getDestinationProject() is not None]

query_kw = {
  'portal_type': 'Assignment Request',
  'simulation_state': 'validated',
  'destination_project__uid': project_uid_list,
  'destination_decision__uid': person.getUid(),
  'function__uid': portal.portal_categories.function.production.customer.getUid()
}
for assignment_request in portal.portal_catalog(**query_kw):
  assignment_request.suspend(comment='Suspended after join %s' % workgroup.getReference())
