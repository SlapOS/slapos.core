from zExceptions import Unauthorized

if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()
person = context
isTransitionPossible = portal.portal_workflow.isTransitionPossible

assignment_project__state_dict = {}

# Close all existing assignments
for assignment in person.contentValues(portal_type="Assignment"):
  if isTransitionPossible(assignment, 'close'):
    assignment.close(comment="Invalidated during migration")
    assignment.reindexObject(activate_kw=activate_kw)

    if assignment.hasDestinationProject():
      # Create at least a customer assignment if user used to view this project
      assignment_project__state_dict[assignment.getDestinationProject()] = False

# For every virtual master handled by this user, create an assignment
for project in portal.portal_catalog(portal_type="Project", destination__uid=person.getUid()):
  assignment = person.newContent(
    portal_type="Assignment",
    title="Manager for %s" % project.getReference(),
    function="production/manager",
    destination_project_value=project.getObject()
  )
  assignment.open(comment="Created during migration")
  assignment.reindexObject(activate_kw=activate_kw)

# For every instance tree's virtual master handled by this user, create an assignment
for instance_tree in portal.portal_catalog(portal_type="Instance Tree",
                                           destination_section__uid=person.getUid(),
                                           validation_state="validated",
                                           group_by=['follow_up_uid']):
  project = instance_tree.getFollowUpValue()
  if project is not None:
    assignment_project__state_dict[project.getRelativeUrl()] = False

for destination_project, is_already_created in assignment_project__state_dict.items():
  project = portal.restrictedTraverse(destination_project)
  if not is_already_created and (project.getValidationState() == 'validated'):

    assignment = person.newContent(
      portal_type="Assignment",
      title="Client for %s" % project.getReference(),
      function="customer",
      role="client",
      destination_project_value=project.getObject()
    )
    assignment.open(comment="Created during migration")
    assignment.reindexObject(activate_kw=activate_kw)
