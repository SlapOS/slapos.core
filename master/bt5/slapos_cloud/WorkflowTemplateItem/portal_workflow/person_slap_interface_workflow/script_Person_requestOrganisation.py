person = state_change['object']
portal = person.getPortalObject()
# Get required arguments
kwargs = state_change.kwargs

# Required args
# Raise TypeError if all parameters are not provided
try:
  organisation_title = kwargs['organisation_title']
except KeyError:
  raise TypeError("Person_requestOrganisation takes exactly 1 argument")

role_id = context.REQUEST.get("role_id", "client")

tag = "%s_%s_%s_OrganisationInProgress" % (person.getUid(),
                               role_id,
                               organisation_title)
if (portal.portal_activities.countMessageWithTag(tag) > 0):
  # The software instance is already under creation but can not be fetched from catalog
  # As it is not possible to fetch informations, it is better to raise an error
  raise NotImplementedError(tag)

organisation_portal_type = "Organisation"
if role_id not in ["client", "host"]:
  raise NotImplementedError

organisation_list = [ i for i in portal.portal_catalog.portal_catalog(
  portal_type=organisation_portal_type,
  title=organisation_title,
  limit=2) if i.getRole() == role_id]

if len(organisation_list) == 2:
  raise NotImplementedError
elif len(organisation_list) == 1:
  context.REQUEST.set("organisation_relative_url", organisation_list[0].getRelativeUrl())
else:
  module = portal.getDefaultModule(portal_type=organisation_portal_type)
  organisation = module.newContent(
    portal_type=organisation_portal_type,
    title=organisation_title,
    role=role_id,
    activate_kw={'tag': tag}
  )
  context.REQUEST.set("organisation_relative_url", organisation.getRelativeUrl())
  organisation.approveRegistration()
