portal_type = context.getPortalType()

if portal_type == "Compute Node":
  return context.getAccessStatus(**kw)

if portal_type == "Instance Tree":
  return context.InstanceTree_getNewsDict(**kw)

if portal_type == "Computer Network":
  return context.ComputerNetwork_getNewsDict(**kw)

raise ValueError("Unsupported Type")
