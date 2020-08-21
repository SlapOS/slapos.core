organisation = state_change["object"]
portal = context.getPortalObject()

if organisation.getValidationState() != "draft":
  return

role = organisation.getRole()
if role not in ["host", "client"]:
  return

if role == "host":
  reference_prefix = "SITE"
else:
  reference_prefix = "O"

if organisation.getReference() in [None, ""]:
  reference = "%s-%s" % (reference_prefix, portal.portal_ids.generateNewId(
    id_group='slap_organisation_reference',
    id_generator='uid'))

  organisation.setReference(reference)

organisation.validate()

user_id = organisation.Base_getOwnerId()
person = context.getPortalObject().portal_catalog.getResultValue(user_id=user_id)
if person is None:
  return

for assignment in person.objectValues(portal_type="Assignment"):
  if assignment.getSubordination() == organisation.getRelativeUrl():
    if assignment.getValidationState() != "open":
      assignment.open()
    return

person.newContent(
  title="Assigment for Site %s" % organisation.getTitle(),
  portal_type="Assignment",
  subordination_value=organisation,
  destination_value=organisation).open()
