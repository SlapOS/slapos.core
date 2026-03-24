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

if not len(project_uid_list):
  return

query_kw = {
  'portal_type': 'Assignment Request',
  'simulation_state': 'validated',
  'destination_project__uid': project_uid_list,
  'destination_decision__uid': person.getUid(),
  'function__uid': portal.portal_categories.function.production.customer.getUid()
}
if len(portal.portal_catalog(**query_kw)) > 0:
  # User still have open 'Assignment Request' seems too early to
  # suspend it, await a bit longer.
  return

instance_tree_to_claim = portal.portal_catalog(
  portal_type='Instance Tree',
  validation_state='validated',
  destination_section__uid=person.getUid(),
  follow_up__uid=project_uid_list)

activate_kw = {
  'tag': "auto_claim_%s_%s" % (workgroup.getId(), person.getId())
}
for instance in instance_tree_to_claim:
  workgroup.activate(**activate_kw).Person_claimSlaposItemSubscription(
    reference=instance.getReference(),
    dialog_id=None,
    activate_kw=activate_kw
  )
