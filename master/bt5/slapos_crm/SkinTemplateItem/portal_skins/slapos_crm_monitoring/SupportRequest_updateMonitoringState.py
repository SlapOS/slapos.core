if context.getSimulationState() == "invalidated":
  return

document = context.getAggregateValue(portal_type="Instance Tree")
if document is None:
  return 

if document.getPortalType() == "Instance Tree":
  if document.getSlapState() == "destroy_requested":
    return context.SupportRequest_updateMonitoringDestroyRequestedState()
