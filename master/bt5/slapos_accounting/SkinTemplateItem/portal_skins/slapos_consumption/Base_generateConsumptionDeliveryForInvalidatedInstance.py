from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

instance = context

if instance.getValidationState() != 'invalidated':
  return

instance.Base_generateConsumptionDeliveryForInstance()
