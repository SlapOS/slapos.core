from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()
assignment_request = context

workgroup = assignment_request.getDestinationValue(portal_type='Workgroup')
person = assignment_request.getDestinationDecisionValue(portal_type='Person')
if (workgroup is None) or (person is None) or (assignment_request.getSimulationState() != 'validated'):
  return

##################################################################
# Search user assignment to automatically close:
# - customer without own instance
# - manager without owning the project
workgroup_assignment_request_list = portal.portal_catalog(
  portal_type='Assignment Request',
  simulation_state='validated',
  destination_decision__uid=workgroup.getUid(),
  destination_project__portal_type='Project',
  function__portal_type='Category',
)
if not len(workgroup_assignment_request_list):
  return

preferred_assignment_category_list = portal.portal_preferences.getPreferredSubscriptionAssignmentCategoryList()
workgroup_project_function_dict = {}
for workgroup_assignment_request in workgroup_assignment_request_list:
  function_uid = workgroup_assignment_request.getFunctionUid()
  project_relative_url = workgroup_assignment_request.getDestinationProject()

  if 'destination_project/%s' % project_relative_url in preferred_assignment_category_list:
    # Do not touch assignment from preferred project,
    # otherwise, it will be recreated by Alarm_createMissingSubscriptionAssignment
    continue

  if function_uid and project_relative_url:
    if project_relative_url in workgroup_project_function_dict:
      workgroup_project_function_dict[project_relative_url].append(function_uid)
    else:
      workgroup_project_function_dict[project_relative_url] = [function_uid]

for project_relative_url in workgroup_project_function_dict:
  project = portal.restrictedTraverse(project_relative_url)

  # If person is current project destination section do nothing
  # and wait for a manual claim
  if project.getDestinationSectionUid() == person.getUid():
    continue

  # If person has an instance, do nothing too
  # and wait for manual claim
  if portal.portal_catalog.getResultValue(
    portal_type='Instance Tree',
    follow_up__uid=project.getUid(),
    destination_section__uid=person.getUid(),
    validation_state='validated'
  ) is not None:
    continue

  for assignment_request in portal.portal_catalog(**{
    'portal_type': 'Assignment Request',
    'simulation_state': 'validated',
    'destination_project__uid': project.getUid(),
    'destination_decision__uid': person.getUid(),
    'function__uid': workgroup_project_function_dict[project_relative_url]
  }):
    assignment_request.suspend(comment='Suspended after joining %s' % workgroup.getReference())
    assignment_request.reindexObject(activate_kw=activate_kw)
