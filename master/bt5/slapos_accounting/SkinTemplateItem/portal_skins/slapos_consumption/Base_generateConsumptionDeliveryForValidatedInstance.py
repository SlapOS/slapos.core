from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

instance = context

if instance.getValidationState() != 'validated':
  return

expiration_date = instance.Base_generateConsumptionDeliveryForInstance()
instance.setExpirationDate(expiration_date)
