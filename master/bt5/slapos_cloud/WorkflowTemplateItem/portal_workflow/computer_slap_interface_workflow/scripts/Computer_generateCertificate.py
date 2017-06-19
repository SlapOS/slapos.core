computer = state_change['object']
# Get required arguments
kwargs = state_change.kwargs

try:
  certificate_signature_request = kwargs["csr"]
except KeyError, e:
  raise TypeError("Computer_generateCertificate takes exactly 1 argument: %s" % str(e))

if computer.getDestinationReference() is not None:
  context.REQUEST.set("computer_certificate", None)
  context.REQUEST.set("computer_certificate_url", None)
  raise ValueError('Certificate still active.')

ca_service = context.getPortalObject().portal_web_services.caucase_adapter
csr_id = ca_service.putCertificateSigningRequest(certificate_signature_request)
# Sign the csr immediately
crt_id, url = ca_service.signCertificate(csr_id)
certificate = ca_service.getCertificate(crt_id)

computer.setDestinationReference(crt_id)

context.REQUEST.set("computer_certificate", certificate)
context.REQUEST.set("computer_certificate_url", url)
