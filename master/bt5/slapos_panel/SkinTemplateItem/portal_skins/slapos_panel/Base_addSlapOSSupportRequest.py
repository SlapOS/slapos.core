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

if context.getPortalType() == 'Instance Tree':
  # Explicitely set the instance owner, so that project's manager
  # can contact the customer
  destination_decision = context.getDestinationSection()
else:
  destination_decision = project.getDestination()

support_request = person.Entity_createTicketFromTradeCondition(
  resource,
  title,
  description,
  portal_type='Support Request',
  destination_decision=destination_decision,
  source_project=project.getRelativeUrl(),
  causality=context.getRelativeUrl()
)

support_request.Ticket_addSlapOSEvent(
  title, description,
  attachment=attachment,
  resource=resource,
  batch=True)

return support_request.Base_redirect()
