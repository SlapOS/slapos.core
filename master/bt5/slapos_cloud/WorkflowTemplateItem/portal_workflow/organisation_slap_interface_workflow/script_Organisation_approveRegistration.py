organisation = state_change["object"]
portal = context.getPortalObject()

role = organisation.getRole()
if role == "host":
  reference_prefix = "SITE"
else:
  reference_prefix = "O"

if organisation.getReference() in [None, ""]:
  reference = "%s-%s" % (reference_prefix, portal.portal_ids.generateNewId(
    id_group='slap_organisation_reference',
    id_generator='uid'))

  organisation.setReference(reference)

if organisation.getValidationState() != "draft":
  return

organisation.validate()

# Get the user id of the context owner.
local_role_list = organisation.get_local_roles()
for group, role_list in local_role_list:
  if 'Owner' in role_list:
    user_id = group
    break

person = portal.portal_catalog.getResultValue(user_id=user_id)

if person is None:
  # Value was created by super user, so there isn't a point on continue
  return

for assignment in person.objectValues(portal_type="Assignment"):
  if assignment.getSubordination() == organisation.getRelativeUrl():
    if assignment.getValidationState() != "open":
      assignment.open()
    return

person.newContent(
  title="Assigment for Organisation (%s) %s" % (organisation.getRole(), organisation.getTitle()),
  portal_type="Assignment",
  subordination_value=organisation,
  destination_value=organisation).open()
