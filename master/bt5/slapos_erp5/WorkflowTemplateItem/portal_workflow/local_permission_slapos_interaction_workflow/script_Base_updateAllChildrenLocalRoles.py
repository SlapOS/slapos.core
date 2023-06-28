"""
This script updates all local roles on sub-objects. It requires Assignor
proxy role since it may be called by owner in draft state.
"""
for child in state_change['object'].contentValues():
  child.updateLocalRolesOnSecurityGroups()
