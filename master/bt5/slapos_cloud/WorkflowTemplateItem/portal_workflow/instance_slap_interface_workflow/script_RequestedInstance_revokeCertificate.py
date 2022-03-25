instance = state_change['object']
portal = instance.getPortalObject()

if instance.getSslKey() is not None or instance.getSslCertificate() is not None:
  instance.edit(ssl_key=None, ssl_certificate=None)

destination_reference = instance.getDestinationReference()
if destination_reference is None:
  raise ValueError('No certificate')

try:
  portal.portal_certificate_authority\
          .revokeCertificate(instance.getDestinationReference())
except ValueError:
  # Ignore already revoked certificates, as OpenSSL backend is
  # non transactional, so it is ok to allow multiple tries to destruction
  # even if certificate was already revoked
  pass
instance.setDestinationReference(None)
