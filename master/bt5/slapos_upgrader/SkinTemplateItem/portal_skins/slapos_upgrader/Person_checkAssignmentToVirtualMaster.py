from zExceptions import Unauthorized

if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()
person = context
isTransitionPossible = portal.portal_workflow.isTransitionPossible

# Close all existing assignments
for assignment in person.contentValues(portal_type="Assignment"):
  if isTransitionPossible(assignment, 'close'):
    assignment.close(comment="Invalidated during migration")
    assignment.reindexObject(activate_kw=activate_kw)

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
    assignment = person.newContent(
      portal_type="Assignment",
      title="Client for %s" % project.getReference(),
      function="customer",
      role="client",
      destination_project_value=project.getObject()
    )
    assignment.open(comment="Created during migration")
    assignment.reindexObject(activate_kw=activate_kw)
