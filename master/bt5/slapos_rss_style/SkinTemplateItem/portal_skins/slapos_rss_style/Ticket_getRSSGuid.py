portal = context.getPortalObject()
latest_event_relative_url = ''
latest_event = context.Ticket_getLatestEvent()
if latest_event:
  latest_event_relative_url = latest_event.getRelativeUrl()

return '{}-{}'.format(
    context.getRelativeUrl(),
    latest_event_relative_url,
)
