"""Hook called when a compute_node object is closed.

We want to reset reference, which is the user login in ERP5Security.
One exception is when a person object is installed from business template.
"""
# Slave Instance don't have user id to be set.
if context.getPortalType() in ["Slave Instance"]:
  return

context.setUserId(None)
context.SoftwareInstance_init()
