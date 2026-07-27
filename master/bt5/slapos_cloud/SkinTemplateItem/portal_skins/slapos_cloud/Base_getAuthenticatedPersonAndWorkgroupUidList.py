portal = context.getPortalObject()

if context.portal_membership.isAnonymousUser():
  return -1

person = portal.portal_membership.getAuthenticatedMember().getUserValue()
if person is None:
  return -1

# Get the list of Workgroup for which user is assigned to
# As user does not have read permission on Assignment,
# use the Assignment Request
uid_list = [x.getDestinationUid() for x in portal.portal_catalog(
  portal_type='Assignment Request',
  destination_decision__uid=person.getUid(),
  destination__portal_type='Workgroup',
)]
uid_list.append(person.getUid())
return uid_list
