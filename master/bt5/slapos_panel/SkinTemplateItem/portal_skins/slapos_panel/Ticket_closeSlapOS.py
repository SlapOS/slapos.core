ticket = context

event = ticket.Ticket_addSlapOSEvent("Close: %s" % ticket.getTitle(), text_content, batch=True)

if context.getPortalType() == "Support Request" and \
    context.getSimulationState() != "invalidated":
  context.invalidate()

if not batch:
  return event.Base_redirect()
