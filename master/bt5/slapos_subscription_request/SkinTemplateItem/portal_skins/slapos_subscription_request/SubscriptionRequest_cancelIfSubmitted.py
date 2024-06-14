from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

subscription_request = context

assert subscription_request.getPortalType() == 'Subscription Request'
assert subscription_request.getSimulationState() == 'submitted' 

item = subscription_request.getAggregateValue()
if item is None:
  resource = subscription_request.getResourceValue()
  raise ValueError('Unsupported resource: %s' % resource.getRelativeUrl())

if item.getValidationState() == "archived":
  subscription_request.cancel()
