if context.getSimulationState() == "invalidated":
  return

document = context.getAggregateValue(portal_type="Hosting Subscription")

if document is None:
  return 

if document.getPortalType() == "Hosting Subscription":
  if document.getSlapState() == "destroy_requested":
    return context.SupportRequest_updateMonitoringDestroyRequestedState()
