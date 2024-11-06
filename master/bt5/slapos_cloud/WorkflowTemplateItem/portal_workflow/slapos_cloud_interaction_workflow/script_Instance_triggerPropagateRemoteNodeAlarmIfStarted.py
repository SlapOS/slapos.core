instance = state_change['object']
partition = instance.getAggregateValue()
if (partition is not None) and (partition.getParentValue().getPortalType() == 'Remote Node') and (instance.getSlapState() != 'start_requested'):
  instance.Base_reindexAndSenseAlarm(['slapos_cloud_propagate_remote_node_instance'])
  partition.Base_reindexAndSenseAlarm(['slapos_cloud_propagate_remote_node_instance'])
