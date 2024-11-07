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
  direction = 'incoming'
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
