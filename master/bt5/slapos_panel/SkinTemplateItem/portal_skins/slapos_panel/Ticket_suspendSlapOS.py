ticket = context

if context.getPortalType() in ["Support Request", "Regularisation Request"] and \
    context.getSimulationState() == "validated":
  context.suspend()

if not batch:
  return ticket.Base_redirect()
