from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

compute_node_dict = {}
compute_partition_dict = {}
for compute_node in compute_node_list:
  news_dict = compute_node.ComputeNode_getNewsDict()
  compute_node_dict[compute_node.getReference()] = news_dict["compute_node"]
  compute_partition_dict[compute_node.getReference()] = news_dict["partition"]

return {"compute_node": compute_node_dict,
        "partition": compute_partition_dict,
        "reference": context.getReference(),
        "portal_type": context.getPortalType(),
        "monitor_url": context.Base_getStatusMonitorUrl()}
