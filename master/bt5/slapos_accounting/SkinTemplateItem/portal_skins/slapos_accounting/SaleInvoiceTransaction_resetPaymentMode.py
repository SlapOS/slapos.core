from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

assert "Sale Invoice Transaction" == context.getPortalType()
assert "stopped" == context.getSimulationState()

# Edit as Manager to workarround security when cancel Sale Invoice Transaction
context.edit(payment_mode=None)
