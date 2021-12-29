organisation = state_change['object']
portal = organisation.getPortalObject()
person = portal.portal_membership.getAuthenticatedMember().getUserValue()

# Get required arguments
kwargs = state_change.kwargs

# Required args
# Raise TypeError if all parameters are not provided
try:
  token_id = kwargs['invitation_token']
except KeyError:
  raise TypeError("Organisation_acceptInvitation takes exactly 1 argument")

try:
  invitation_token = portal.invitation_token_module[token_id]
except KeyError:
  raise ValueError("The Invitation Token can't be found, please review the URL.")

if person is None:
  message_str = "Please login before access the invitation link."
  raise ValueError(message_str)

if invitation_token.getPortalType() != "Invitation Token":
  message_str = "The Invitation Token can't be found, please review the URL."
  raise ValueError(message_str)

if invitation_token.getValidationState() != "validated":
  message_str = "The Invitation Token was already used and it cannot be reused, please ask a new one."
  raise ValueError(message_str)

if invitation_token.getSourceValue() == person:
  message_str = "Invitation Token cannot be used by the same user that generated the token!"
  raise ValueError(message_str)


for assignment in person.objectValues(portal_type="Assignment"):
  if assignment.getSubordination() == organisation.getRelativeUrl() and \
    assignment.getValidationState() == "open":
    invitation_token.invalidate(comment="User already has assignment to the Person")
    break

if invitation_token.getValidationState() == "validated":
  person.newContent(
    title="Assigment for Organisation (%s) %s" % (organisation.getRole(), organisation.getTitle()),
    portal_type="Assignment",
    subordination_value=organisation,
    destination_value=organisation).open()

  invitation_token.invalidate()
