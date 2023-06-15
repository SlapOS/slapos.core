from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

def get_compute_partition_dict():
  compute_node_dict =  context.getAccessStatus()
  compute_partition_dict = context.getComputePartitionNewsDict()

  return {"compute_node": compute_node_dict,
          "partition": compute_partition_dict,
          "portal_type": compute_node_dict['portal_type'],
          "reference": compute_node_dict['reference'],
          "monitor_url": context.Base_getStatusMonitorUrl()}

return get_compute_partition_dict()
