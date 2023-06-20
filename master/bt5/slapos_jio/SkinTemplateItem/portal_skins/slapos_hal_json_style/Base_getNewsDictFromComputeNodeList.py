from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

node_dict = {}
partition_dict = {}
for compute_node in compute_node_list:
  reference = compute_node.getReference()
  node_dict[reference] = compute_node.getAccessStatus()
  partition_dict[reference] = compute_node.getComputePartitionNewsDict()

return {"compute_node": node_dict,
        "partition": partition_dict,
        "reference": context.getReference(),
        "portal_type": context.getPortalType(),
        "monitor_url": context.Base_getStatusMonitorUrl(compute_node_list=compute_node_list)}
