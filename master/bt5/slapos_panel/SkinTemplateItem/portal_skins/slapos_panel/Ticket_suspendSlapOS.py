ticket = context

if context.getPortalType() in ["Support Request", "Regularisation Request"] and \
    context.getSimulationState() == "validated":
  context.suspend()

return ticket.Base_redirect()
