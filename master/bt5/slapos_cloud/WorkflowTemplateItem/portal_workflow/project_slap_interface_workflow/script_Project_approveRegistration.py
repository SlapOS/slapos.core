project = state_change["object"]
from DateTime import DateTime

portal = context.getPortalObject()

if project.getValidationState() != "draft":
  return

if project.getReference() in [None, ""]:
  reference = "PROJ-%s" % portal.portal_ids.generateNewId(
    id_group='slap_project_reference',
    id_generator='uid', default=1)
  project.setReference(reference)


# Get the user id of the context owner.
local_role_list = project.get_local_roles()
for group, role_list in local_role_list:
  if 'Owner' in role_list:
    user_id = group
    break

person = portal.portal_catalog.getResultValue(user_id=user_id)

if person is None:
  # Value was created by super user, so there isn't a point on continue
  return

for assignment in person.objectValues(portal_type="Assignment"):
  if assignment.getDestinationProject() == project.getRelativeUrl():
    if assignment.getValidationState() != "open":
      assignment.open()
    return

person.newContent(
  title="Assigment for Project %s" % project.getTitle(),
  portal_type="Assignment",
  destination_project=project.getRelativeUrl()).open()

project.edit(start_date=DateTime())
project.validate()
