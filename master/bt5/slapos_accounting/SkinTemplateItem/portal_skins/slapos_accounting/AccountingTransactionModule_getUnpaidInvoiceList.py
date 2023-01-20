portal = context.getPortalObject()
portal_membership=portal.portal_membership

user = portal_membership.getAuthenticatedMember().getUserValue()

def wrapWithShadow(user):
  return user.Entity_getOutstandingAmountList(
    parent_portal_type="Sale Invoice Transaction")

return user.Person_restrictMethodAsShadowUser(
  shadow_document=user,
  callable_object=wrapWithShadow,
  argument_list=[user])
