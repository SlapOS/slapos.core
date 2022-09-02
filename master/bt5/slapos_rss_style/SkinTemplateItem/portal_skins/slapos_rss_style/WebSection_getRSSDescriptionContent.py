event = context.Ticket_getLastEvent()
if event:
  return event.getTextContent()

return context.getDescription()
