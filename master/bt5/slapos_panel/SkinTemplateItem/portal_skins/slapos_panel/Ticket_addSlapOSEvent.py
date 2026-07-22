from Products.ERP5Type.Errors import UnsupportedWorkflowMethod

REQUEST = context.REQUEST
portal = context.getPortalObject()
ticket = context
person = portal.portal_membership.getAuthenticatedMember().getUserValue()
person_relative_url = person.getRelativeUrl()

# Max ~3Mb
if int(REQUEST.getHeader('Content-Length', 0)) > 3145728:
  REQUEST.RESPONSE.setStatus(413)
  return ""

event_kw = {}
direction = 'outgoing'

if person_relative_url == ticket.getDestination(portal_type='Person'):
  direction = 'incoming'

elif ticket.getDestination(portal_type="Workgroup"):
  # Destination is preserved as Workgroup.
  event_kw['destination'] = ticket.getDestination(portal_type="Workgroup")

  # check if the user is a workgroup member
  workgroup = ticket.getDestinationValue(
    portal_type="Workgroup",
    checked_permission='View')

  if workgroup is not None:
    if person.Base_isPersonFromWorkgroup(person, workgroup):
      direction = 'incoming'

if resource is None:
  resource = ticket.getResource()

event = ticket.Ticket_createProjectEvent(
  title, direction, 'Web Message',
  resource,
  text_content=text_content,
  content_type='text/plain',
  attachment=attachment,
  source=person_relative_url,
  **event_kw
)

if ticket.getPortalType() == 'Support Request':
  try:
    ticket.validate()
  except (AttributeError, UnsupportedWorkflowMethod):
    pass

if batch:
  return event
return event.Base_redirect()
