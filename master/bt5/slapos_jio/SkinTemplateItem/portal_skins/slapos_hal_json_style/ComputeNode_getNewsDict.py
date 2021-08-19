from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

def get_compute_partition_dict(reference):
  compute_node_dict =  context.Base_getNewsDict(context)
  compute_partition_dict = { }
  for compute_partition in context.objectValues(portal_type="Compute Partition"):
    software_instance = compute_partition.getAggregateRelatedValue(portal_type="Software Instance")
    if software_instance is not None:
      compute_partition_dict[compute_partition.getTitle()] = context.Base_getNewsDict(software_instance)

  return {"compute_node": compute_node_dict,
          "partition": compute_partition_dict}

# Use Cache here, at least transactional one.
return get_compute_partition_dict(context.getReference())
