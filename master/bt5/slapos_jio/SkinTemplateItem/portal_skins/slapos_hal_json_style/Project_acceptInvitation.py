from zExceptions import Unauthorized
portal = context.getPortalObject()

person = portal.portal_membership.getAuthenticatedMember().getUserValue()
if person is None:
  message_str = "Please login before access the invitation link."
  return context.REQUEST.RESPONSE.redirect(
    context.getWebSectionValue().absolute_url() + \
    "/join_form?portal_status_message=" + \
    context.Base_translateString(message_str))

def redirect(message, message_type):
  return context.REQUEST.RESPONSE.redirect(
    context.getWebSiteValue().absolute_url() + \
    "/#/?page=slap_notify_and_redirect&message_type=%s" % message_type + \
    "&portal_status_message=%s" % context.Base_translateString(message))

if invitation_token is None:
  message_str = "The Invitation Token is not present on the URL, please review the URL."
  return redirect(message_str, "error")

if context.getPortalType() != "Project":
  raise Unauthorized("Context is not an Project, please review your URL.")

try:
  invitation_token = portal.invitation_token_module[invitation_token]
except KeyError:
  message_str = "The Invitation Token can't be found, please review the URL."
  return redirect(message_str, "error")

if invitation_token.getPortalType() != "Invitation Token":
  message_str = "The Invitation Token can't be found, please review the URL."
  return redirect(message_str, "error")

if invitation_token.getValidationState() != "validated":
  message_str = "The Invitation Token was already used and it cannot be reused, please ask a new one."
  return redirect(message_str, "error")

if invitation_token.getSourceValue() == person:
  message_str = "Invitation Token cannot be used by the same user that generated the token!"
  return redirect(message_str, "error")

for assignment in person.objectValues(portal_type="Assignment"):
  if assignment.getDestinationProject() == context.getRelativeUrl():
    invitation_token.invalidate(comment="User already has assignment to the Person")
    message_str = "You sucessfully join a new project: %s." % context.getTitle()
    return redirect(message_str, "success")
    
person.newContent(
  title="Assigment for Project %s" % context.getTitle(),
  portal_type="Assignment",
  destination_project_value=context).open()

invitation_token.invalidate()

message_str = "You sucessfully join a new project: %s." % context.getTitle()
return redirect(message_str, "success")
