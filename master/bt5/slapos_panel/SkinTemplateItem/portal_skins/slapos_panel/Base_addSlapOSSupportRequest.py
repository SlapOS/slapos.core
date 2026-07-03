portal = context.getPortalObject()
REQUEST = context.REQUEST
entity = portal.portal_membership.getAuthenticatedMember().getUserValue()

# Max ~3Mb
if int(REQUEST.getHeader('Content-Length', 0)) > 3145728:
  REQUEST.RESPONSE.setStatus(413)
  return ""

if context.getPortalType() == 'Project':
  project = context
else:
  project = context.getFollowUpValue()

if context.getPortalType() == "Instance Tree":
  workgroup = context.getDestinationSection(
    portal_type='Workgroup', checked_permission='View')
  if workgroup is not None:
    entity = context.getDestinationSectionValue(portal_type='Workgroup')

support_request = entity.Entity_createTicketFromTradeCondition(
  resource,
  title,
  description,
  portal_type='Support Request',
  source_project=project.getRelativeUrl(),
  causality=context.getRelativeUrl()
)

support_request.Ticket_addSlapOSEvent(
  title, description,
  attachment=attachment,
  resource=resource,
  batch=True)

return support_request.Base_redirect()
