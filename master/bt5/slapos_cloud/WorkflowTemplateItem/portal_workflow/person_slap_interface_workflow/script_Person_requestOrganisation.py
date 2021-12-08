person = state_change['object']
portal = person.getPortalObject()
# Get required arguments
kwargs = state_change.kwargs

# Required args
# Raise TypeError if all parameters are not provided
try:
  organisation_title = kwargs['organisation_title']
except KeyError:
  raise TypeError, "Person_requestOrganisation takes exactly 1 argument"

role_id = context.REQUEST.get("role_id", "client")

tag = "%s_%s_%s_OrganisationInProgress" % (person.getUid(),
                               role_id,
                               organisation_title)
if (portal.portal_activities.countMessageWithTag(tag) > 0):
  # The software instance is already under creation but can not be fetched from catalog
  # As it is not possible to fetch informations, it is better to raise an error
  raise NotImplementedError(tag)

organisation_portal_type = "Organisation"
organisation_list = portal.portal_catalog.portal_catalog(
  portal_type=organisation_portal_type,
  title=organisation_title,
  # check if this works
  role_id=role_id,
  limit=2)

if len(organisation_list) == 2:
  raise NotImplementedError
elif len(organisation_list) == 1:
  context.REQUEST.set("organisation_relative_url", organisation_list[0].getRelativeUrl())
  context.REQUEST.set("organisation_reference", organisation_list[0].getReference())
else:
  module = portal.getDefaultModule(portal_type=organisation_portal_type)
  organisation = module.newContent(
    portal_type=organisation_portal_type,
    title=organisation_title,
    role=role_id,
    activate_kw={'tag': tag}
  )
  context.REQUEST.set("organisation_relative_url", organisation.getRelativeUrl())
  context.REQUEST.set("organisation_reference", organisation.getReference())

  organisation.approveRegistration()
