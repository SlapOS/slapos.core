ticket = state_change["object"]
from DateTime import DateTime
portal = ticket.getPortalObject()

# Get required arguments
kwargs = state_change.kwargs

# Required args
# Raise TypeError if all parameters are not provided
try:
  message_title = kwargs['message_title']
  message = kwargs['message']
except KeyError:
  raise TypeError("Ticket_notify takes exactly 2 arguments")

resource = portal.service_module.slapos_crm_information.getRelativeUrl()

# create Web message if needed for this ticket
last_event = ticket.SupportRequest_getLastEvent(message_title)
if last_event:
  # User has already been notified for this problem.
  ticket.REQUEST.set("ticket_notified_item", last_event)
  return

transactional_event = ticket.REQUEST.get("ticket_notified_item", None)

if transactional_event is not None:
  if (transactional_event.getFollowUpUid() == ticket.getUid()) and \
    (transactional_event.getTitle() == message_title):
    ticket.REQUEST.set("ticket_notified_item", transactional_event)
    return

template = portal.restrictedTraverse(
        portal.portal_preferences.getPreferredWebMessageTemplate())

event = template.Base_createCloneDocument(batch_mode=1)
event.edit(
  title=message_title,
  text_content=message,
  start_date = DateTime(),
  resource = resource,
  source=ticket.getDestinationDecision(),
  destination=ticket.getSource(),
  follow_up=ticket.getRelativeUrl(),
)
# If the template is a Mail Template it will just sent the
# email to its destination. If it is an Web Message it will
# just ignore.
event.start(send_mail=True)
event.stop()
event.deliver()

ticket.serialize()
ticket.REQUEST.set("ticket_notified_item", event)
