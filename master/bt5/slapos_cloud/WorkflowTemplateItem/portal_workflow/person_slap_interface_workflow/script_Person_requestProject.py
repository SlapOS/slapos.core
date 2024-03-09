person = state_change['object']
portal = person.getPortalObject()
# Get required arguments
kwargs = state_change.kwargs

# Required args
# Raise TypeError if all parameters are not provided
try:
  project_title = kwargs['project_title']
except KeyError:
  raise TypeError("Person_requestProject takes exactly 1 argument")

tag = "%s_%s_ProjectInProgress" % (person.getUid(), 
                               project_title)
if (portal.portal_activities.countMessageWithTag(tag) > 0):
  # The software instance is already under creation but can not be fetched from catalog
  # As it is not possible to fetch informations, it is better to raise an error
  raise NotImplementedError(tag)

project_portal_type = "Project"
project_list = portal.portal_catalog.portal_catalog(
  portal_type=project_portal_type, title=project_title, limit=2)

if len(project_list) == 2:
  raise NotImplementedError
elif len(project_list) == 1:
  context.REQUEST.set("project_relative_url", project_list[0].getRelativeUrl())
  context.REQUEST.set("project_reference", project_list[0].getReference())
else:
  module = portal.getDefaultModule(portal_type=project_portal_type)
  project = module.newContent(
    portal_type=project_portal_type,
    title=project_title,
    destination_decision_value=person,
    activate_kw={'tag': tag}
  )
  context.REQUEST.set("project_relative_url", project.getRelativeUrl())
  context.REQUEST.set("project_reference", project.getReference())

  project.approveRegistration()
