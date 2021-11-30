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

try:
  context.acceptInvitation(invitation_token=invitation_token)
except ValueError as e:
  return redirect(context.Base_translateString(e), "error")

message_str = context.Base_translateString("You sucessfully join a new project: ") 
message_str += context.getTitle()
return redirect(message_str, "success")
