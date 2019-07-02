from zExceptions import Unauthorized
portal = context.getPortalObject()

if invitation_token is None:
  raise ValueError("Invitation Token is required")

if context.getPortalType() != "Project":
  raise Unauthorized("Context is not an Organisation")

person = portal.portal_membership.getAuthenticatedMember().getUserValue()

if person is None:
  raise ValueError("You must be logged in!")

try:
  invitation_token = portal.invitation_token_module[invitation_token]
except KeyError:
  raise ValueError("Invitation Token is not found.")

if invitation_token.getPortalType() != "Invitation Token":
  raise ValueError("Invitation Token is not found.")

if invitation_token.getValidationState() != "validated":
  raise ValueError("Invitation Token was already used.")

if invitation_token.getSourceValue() == person:
  raise ValueError("Invitation Token cannot be used by the same user that generated the token!")

for assignment in person.objectValues(portal_type="Assignment"):
  if assignment.getSubordination() == context.getRelativeUrl():
    invitation_token.invalidate(comment="User already has assignment to the Person")
    return "Already had stuff"

person.newContent(
  title="Assigment for Project %s" % context.getTitle(),
  portal_type="Assignment",
  destination_project_value=context).open()

invitation_token.invalidate()

return 'Go charlie'
