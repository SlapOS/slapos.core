from zExceptions import Unauthorized
from DateTime import DateTime
if REQUEST is not None:
  raise Unauthorized

instance = context

if instance.getValidationState() != 'invalidated':
  return

instance.Base_generateConsumptionDeliveryForInstance()
instance.setExpirationDate(DateTime())
