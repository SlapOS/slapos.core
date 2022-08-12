from Products.ERP5Type.Errors import UnsupportedWorkflowMethod

portal = context.getPortalObject()
ticket = context
person = portal.portal_membership.getAuthenticatedMember().getUserValue()
person_relative_url = person.getRelativeUrl()

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
  source=person_relative_url
)

try:
  ticket.validate()
except UnsupportedWorkflowMethod:
  pass

if batch:
  return event
return event.Base_redirect()
