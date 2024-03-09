ticket = state_change["object"]
from DateTime import DateTime
portal = context.getPortalObject()
# Get required arguments
kwargs = state_change.kwargs

# Required args
# Raise TypeError if all parameters are not provided
try:
  title = kwargs['event_title']
  text_content = kwargs['event_content']
  source = kwargs['event_source']
except KeyError:
  raise TypeError("Ticket_requestEvent takes at exactly 3 argument")

web_message = portal.event_module.newContent(
  portal_type="Web Message",
  start_date = DateTime(),
  title=title,
  text_content=text_content,
  source=source,
  content_type="text/plain",
  destination=ticket.getSource(),
  resource=ticket.getResource(),
  follow_up=ticket.getRelativeUrl()
)

web_message.stop(comment="Submitted from the renderjs app")
if portal.portal_workflow.isTransitionPossible(ticket, "validate"):
  ticket.validate(comment="See %s" % web_message.getRelativeUrl())

ticket.REQUEST.set("event_relative_url", web_message.getRelativeUrl())
