instance = state_change['object']
if instance.getTitle().startswith('_remote_'):
  return instance.Base_reindexAndSenseAlarm(['slapos_cloud_propagate_remote_node_instance'])
