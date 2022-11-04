portal = context.getPortalObject()
portal_membership=portal.portal_membership

user = portal_membership.getAuthenticatedMember().getUserValue()

def wrapWithShadow():
  return [i.getCausalityValue(portal_type="Sale Invoice Transaction") for i in context.getPortalObject().portal_catalog(
    portal_type="Payment Transaction",
    simulation_state="started",
    destination_section_uid=user.getUid(),
    default_causality_portal_type="Sale Invoice Transaction",
    default_causality_simulation_state="stopped",
  )]

return user.Person_restrictMethodAsShadowUser(
  shadow_document=user,
  callable_object=wrapWithShadow,
  argument_list=[])
