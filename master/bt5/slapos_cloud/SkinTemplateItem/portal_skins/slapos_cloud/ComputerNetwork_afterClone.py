"""Hook called when a compute_node object is closed.

We want to reset reference, which is the user login in ERP5Security.
One exception is when a person object is installed from business template.
"""
if context.getPortalType() != "Computer Network":
  return
context.ComputerNetwork_init()
