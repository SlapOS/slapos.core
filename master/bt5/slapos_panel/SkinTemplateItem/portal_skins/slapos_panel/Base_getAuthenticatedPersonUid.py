portal = context.getPortalObject()

if context.portal_membership.isAnonymousUser():
  return -1

person = portal.portal_membership.getAuthenticatedMember().getUserValue()
if person is None:
  return -1

return person.getUid()
