if context.ComputeNode_hasContactedRecently():
  return

return context.ComputeNode_checkAndUpdateAllocationScope(
  target_allocation_scope = 'close/outdated',
  notification_message_reference='slapos-crm-compute-node-allocation-scope-closed.notification',
  check_service_provider=False,
  force=True)
