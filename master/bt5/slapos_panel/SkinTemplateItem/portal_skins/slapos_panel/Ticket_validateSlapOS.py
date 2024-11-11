ticket = context

if context.getPortalType() == "Regularisation Request" and \
    context.getSimulationState() == "suspended":
  context.validate()

return ticket.Base_redirect()
