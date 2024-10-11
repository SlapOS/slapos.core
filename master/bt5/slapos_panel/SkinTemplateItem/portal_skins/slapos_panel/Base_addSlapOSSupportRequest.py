portal = context.getPortalObject()
REQUEST = context.REQUEST
person = portal.portal_membership.getAuthenticatedMember().getUserValue()

# Max ~3Mb
if int(REQUEST.getHeader('Content-Length', 0)) > 3145728:
  REQUEST.RESPONSE.setStatus(413)
  return ""

if context.getPortalType() == 'Project':
  project = context
else:
  project = context.getFollowUpValue()
support_request = project.Project_createTicketWithCausality(
  'Support Request',
  title,
  description,
  causality=context.getRelativeUrl(),
  destination_decision=person.getRelativeUrl()
)

support_request.Ticket_addSlapOSEvent(title, description, attachment=attachment, resource=resource, batch=True)

return support_request.Base_redirect()
