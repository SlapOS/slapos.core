instance = state_change['object']
partition = instance.getAggregateValue()
if (partition is not None) and (partition.getParentValue().getPortalType() == 'Remote Node'):
  partition.Base_reindexAndSenseAlarm(['slapos_cloud_propagate_remote_node_instance'])
