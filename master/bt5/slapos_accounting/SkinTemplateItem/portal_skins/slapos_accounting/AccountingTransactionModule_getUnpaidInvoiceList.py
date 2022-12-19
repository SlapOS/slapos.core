portal = context.getPortalObject()
portal_membership=portal.portal_membership

user = portal_membership.getAuthenticatedMember().getUserValue()

def wrapWithShadow(user):
  return user.Entity_getOutstandingAmountList()

return user.Person_restrictMethodAsShadowUser(
  shadow_document=user,
  callable_object=wrapWithShadow,
  argument_list=[user])
