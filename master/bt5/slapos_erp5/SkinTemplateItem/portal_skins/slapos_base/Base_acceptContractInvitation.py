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
  message_str = "The Contract Token is not present on the URL, please review the URL."
  return redirect(message_str, "error")

try:
  invitation_token_document = portal.invitation_token_module[invitation_token]
except KeyError:
  message_str = "The Contract Token can't be found, please review the URL."
  return redirect(message_str, "error")

if invitation_token_document.getPortalType() != "Contract Invitation Token":
  message_str = "The Contract Token can't be found, please review the URL."
  return redirect(message_str, "error")

if invitation_token_document.getValidationState() != "validated":
  message_str = "The Contract Token was already used and it cannot be reused, please ask a new one."
  return redirect(message_str, "error")

if invitation_token_document.getSourceValue() is not None and invitation_token.getSourceValue() != person:
  message_str = "Contract Token cannot be used by your user as it is linked to a specific user!"
  return redirect(message_str, "error")

person.Base_acceptContractInvitation(invitation_token_document)

message_str = "Your contract had been updated."
return redirect(message_str, "success")
