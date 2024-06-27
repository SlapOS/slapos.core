from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

for uid, secure_service_relative_url in context.Base_getSupportedExternalPaymentList():
  if currency_uid == uid and secure_service_relative_url is not None:
    return 1
return 0
