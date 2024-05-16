ticket = context

if context.getPortalType() == "Support Request" and \
    context.getSimulationState() == "validated":
  context.suspend()

return ticket.Base_redirect()
