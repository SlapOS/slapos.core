event = context.Ticket_getLastEvent()
if event:
  return event.getModificationDate()

return context.getModificationDate()
