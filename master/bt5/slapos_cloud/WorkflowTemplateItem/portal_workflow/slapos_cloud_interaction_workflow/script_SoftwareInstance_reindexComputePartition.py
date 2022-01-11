instance = state_change['object']
partition = instance.getAggregateValue(portal_type="Compute Partition")
if partition is not None:

  active_object = partition.activate(
      after_path_and_method_id=(instance.getPath(), ('immediateReindexObject', 'recursiveImmediateReindexObject')))
  if partition.getParentValue().getPortalType() == 'Remote Node':
    active_object.Base_reindexAndSenseAlarm(['slapos_cloud_propagate_remote_node_instance'])
  else:
    active_object.reindexObject()
