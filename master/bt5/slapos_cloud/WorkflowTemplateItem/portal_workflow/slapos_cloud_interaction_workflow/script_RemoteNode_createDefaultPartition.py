remote_node = state_change['object']

if remote_node.getValidationState() == 'draft':
  partition_id = 'SHARED_REMOTE'
  if partition_id not in remote_node.objectIds():
    partition = remote_node.newContent(
      portal_type='Compute Partition',
      reference='shared_partition',
      id=partition_id
    )
    partition.markFree()
    partition.markBusy()
    partition.validate()
