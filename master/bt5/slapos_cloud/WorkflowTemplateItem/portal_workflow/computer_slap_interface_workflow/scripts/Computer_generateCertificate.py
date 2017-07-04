computer = state_change['object']
# Get required arguments
kwargs = state_change.kwargs

try:
  certificate_signature_request = kwargs["certificate_request"]
except KeyError, e:
  raise TypeError("Computer_generateCertificate takes exactly 1 argument: %s" % str(e))

certificate_portal_type = "Certificate Access ID"
certificate_id_list = [x for x in
  computer.contentValues(portal_type=certificate_portal_type)
  if x.getValidationState() == 'validated']

if len(certificate_id_list):
  context.REQUEST.set("computer_certificate", None)
  context.REQUEST.set("computer_certificate_url", None)
  raise ValueError('Certificate still active.')

ca_service = context.getPortalObject().portal_web_services.caucase_adapter
csr_id = ca_service.putCertificateSigningRequest(certificate_signature_request)
# Sign the csr immediately
crt_id, url = ca_service.signCertificate(
      csr_id,
      subject={'CN': computer.getReference()})
certificate = ca_service.getCertificate(crt_id)

certificate_id = computer.newContent(
  portal_type=certificate_portal_type,
  reference=crt_id,
  url_string=url)

certificate_id.validate()

context.REQUEST.set("computer_certificate", certificate)
context.REQUEST.set("computer_certificate_url", url)
