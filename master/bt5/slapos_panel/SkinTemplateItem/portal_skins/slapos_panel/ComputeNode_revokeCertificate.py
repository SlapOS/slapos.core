from Products.ERP5Type.Message import translateString

try:
  context.revokeCertificate()
except ValueError:
  message = "This Compute Node has no certificate to revoke."
  status = 'warning'
else:
  message = "Certificate is Revoked."
  status = 'success'


return context.Base_redirect(
  keep_items={
    'portal_status_message': translateString(message),
    'portal_status_level': status
  }
)
