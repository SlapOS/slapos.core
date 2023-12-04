from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()
service_reference = portal.portal_preferences.getPreferredWechatPaymentServiceReference()

if not service_reference:
  return

try:
  payment_service = portal.portal_secure_payments.find(
    service_reference=service_reference)
except ValueError:
  # If service is not found, return None
  # this might allow the side handle disabled service configuration.
  return 

return payment_service.getRelativeUrl()
