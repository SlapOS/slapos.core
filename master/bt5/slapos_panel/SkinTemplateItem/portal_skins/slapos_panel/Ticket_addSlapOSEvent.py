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

if person_relative_url == ticket.getDestination():
  # ticket to a person
  direction = 'incoming'
elif len(portal.portal_catalog(
  portal_type='Assignment Request',
  simulation_state='validated',
  destination__relative_url=ticket.getDestination(),
  destination_decision__uid=person.getUid(),
  limit=1
)) == 1:
  # current person is member of ticket workgroup
  direction = 'incoming'
  # Keep workgroup as source, in order to allow
  # all workgroup members to see the event
  person_relative_url = ticket.getDestination()
else:
  direction = 'outgoing'

if resource is None:
  resource = ticket.getResource()

event = ticket.Ticket_createProjectEvent(
  title, direction, 'Web Message',
  resource,
  text_content=text_content,
  content_type='text/plain',
  attachment=attachment,
  source=person_relative_url
)

if ticket.getPortalType() == 'Support Request':
  try:
    ticket.validate()
  except (AttributeError, UnsupportedWorkflowMethod):
    pass

if batch:
  return event
return event.Base_redirect()
