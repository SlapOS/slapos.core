compute_node = state_object["object"]
allocation_scope = compute_node.getAllocationScope()

upgrade_scope = compute_node.getUpgradeScope()

if allocation_scope in ['open/public', 'open/subscription']:
  # Public compute_node capacity is handle by an alarm
  capacity_scope = 'close'
  monitor_scope = 'enabled'
  if upgrade_scope in [None, 'ask_confirmation']:
    upgrade_scope = 'auto'

elif allocation_scope == 'open/personal':
  capacity_scope = 'open'
  # Keep the same.
  monitor_scope = compute_node.getMonitorScope("disabled")
  if upgrade_scope is None:
    upgrade_scope = 'ask_confirmation'
else:
  monitor_scope = 'disabled'
  capacity_scope = 'close'

compute_node.edit(
  capacity_scope=capacity_scope,
  monitor_scope=monitor_scope,
  upgrade_scope=upgrade_scope)
