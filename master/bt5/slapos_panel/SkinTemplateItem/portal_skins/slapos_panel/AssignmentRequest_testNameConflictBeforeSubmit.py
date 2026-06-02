from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()
assignment_request = context
workgroup = assignment_request.getDestinationValue(portal_type='Workgroup')
person = assignment_request.getDestinationDecisionValue(portal_type='Person')
no_conflict_comment = "%s (No Conflict)" % comment

if workgroup is None or person is None:
  return assignment_request.submit(comment=no_conflict_comment)

workgroup_assignment_request_list = portal.portal_catalog(
    portal_type='Assignment Request',
    simulation_state='validated',
    destination_decision__uid=workgroup.getUid(),
    function__uid=portal.portal_categories.function.customer.getUid()
  )

if not len(workgroup_assignment_request_list):
  return assignment_request.submit(comment=no_conflict_comment)

project_uid_list = [
  x.getDestinationProjectUid() for x in workgroup_assignment_request_list
    if x.getDestinationProject() is not None]

query_kw = {
  'portal_type': 'Instance Tree',
  'validation_state': 'validated',
  'follow_up__uid': project_uid_list
}

person_instance_tree_title_list = [i.title for i in portal.portal_catalog(
     destination_section__uid=person.getUid(), **query_kw)]

if not person_instance_tree_title_list:
  return assignment_request.submit(comment=no_conflict_comment)

instance_with_name_conflict = portal.portal_catalog(
     destination_section__uid=workgroup.getUid(),
     title=person_instance_tree_title_list,
     limit=5, **query_kw)

if not len(instance_with_name_conflict):
  return assignment_request.submit(comment=no_conflict_comment)

comment += ' (Conflict detected on %s)' % (', '.join([i.title for i in instance_with_name_conflict]))
last_workflow_item = portal.portal_workflow.getInfoFor(ob=assignment_request,
                                                        name='comment', wf_id='edit_workflow')
if last_workflow_item != comment:
  portal.portal_workflow.doActionFor(
    assignment_request, action='edit_action', comment=comment)
