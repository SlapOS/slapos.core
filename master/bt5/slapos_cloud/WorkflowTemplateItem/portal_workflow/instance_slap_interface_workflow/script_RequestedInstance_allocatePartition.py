instance = state_change['object']
assert instance.getPortalType() in ["Software Instance", "Slave Instance"]
portal = instance.getPortalObject()
# Get required arguments
kwargs = state_change.kwargs

# Required args
# Raise TypeError if all parameters are not provided
try:
  compute_partition_url = kwargs['compute_partition_url']
except KeyError:
  raise TypeError("RequestedInstance_allocatePartition takes exactly 1 argument")

assert instance.getAggregateValue() is None
compute_partition = portal.restrictedTraverse(compute_partition_url)
assert compute_partition.getPortalType() == "Compute Partition"

instance.edit(aggregate_value=compute_partition, activate_kw={'tag': 'allocate_%s' % compute_partition_url})

compute_node = compute_partition.getParentValue()

compute_node.ComputeNode_checkAndUpdateCapacityScope(
  allocated_instance=instance
)
