portal = context.getPortalObject()
person = portal.portal_membership.getAuthenticatedMember().getUserValue()

if context.getPortalType() == 'Project':
  project = context
else:
  project = context.getFollowUpValue()
support_request = project.Project_createSupportRequestWithCausality(
  title,
  description,
  causality=context.getRelativeUrl(),
  destination_decision=person.getRelativeUrl()
)

support_request.Ticket_addSlapOSEvent(title, description, resource=resource, batch=True)

return support_request.Base_redirect()
