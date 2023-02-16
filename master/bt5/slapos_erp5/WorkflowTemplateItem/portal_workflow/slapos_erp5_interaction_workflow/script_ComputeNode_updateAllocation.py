compute_node = state_object["object"]

edit_kw = {}

# Automatically close the capacity whenever the allocation scope
# changes, and let the alarm update it later, whenever the 
# allocation scope is open.
if compute_node.getCapacityScope() != "close":
  edit_kw['capacity_scope'] = 'close'

if compute_node.getMonitorScope() is None:
  edit_kw['monitor_scope'] = 'enabled'

if compute_node.getAllocationScope() == "close/forever":
  edit_kw['monitor_scope'] = 'disabled'

if edit_kw:
  compute_node.edit(**edit_kw)
