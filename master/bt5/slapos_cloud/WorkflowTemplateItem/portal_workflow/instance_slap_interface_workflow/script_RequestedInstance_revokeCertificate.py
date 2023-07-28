instance = state_change['object']
portal = instance.getPortalObject()

if instance.getSslKey() is not None or instance.getSslCertificate() is not None:
  instance.edit(ssl_key=None, ssl_certificate=None)

no_certificate = True
for certificate_login in instance.objectValues(
  portal_type=["Certificate Login"]):
  if certificate_login.getValidationState() == "validated":
    certificate_login.invalidate()
    no_certificate = False

if no_certificate:
  raise ValueError('No certificate')
