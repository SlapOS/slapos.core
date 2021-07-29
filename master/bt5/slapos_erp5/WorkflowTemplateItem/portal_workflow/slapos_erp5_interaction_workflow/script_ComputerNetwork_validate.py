computer_network = state_object["object"]

portal = context.getPortalObject()
person = portal.portal_membership.getAuthenticatedMember().getUserValue()

if person is not None and computer_network.getValidationState() == "draft":
  computer_network.edit(
    source_administration=person.getRelativeUrl()
  )

if computer_network.getValidationState() == "draft":
  computer_network.validate()
