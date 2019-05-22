portal = context.getPortalObject()
person = portal.portal_membership.getAuthenticatedMember().getUserValue()

if context.getPortalType() == "Support Request" and \
    person.getRelativeUrl() == context.getDestinationDecision() and \
    context.getValidationState() != "invalidated":
  context.invalidate()
