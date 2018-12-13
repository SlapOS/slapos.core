result_list = []
simulation_state_list = ["validated", "suspended", "confirmed", "started", "stopped"]
for value in context.getAggregateRelatedValueList(portal_type=["Support Request", "Upgrade Decision Line"]):
  if value.getPortalType() == "Upgrade Decision Line":
    result = value.getParent()
  else:
    result = value
  if result.getSimulationState()  in simulation_state_list:
    result_list.append(result)

return result_list
