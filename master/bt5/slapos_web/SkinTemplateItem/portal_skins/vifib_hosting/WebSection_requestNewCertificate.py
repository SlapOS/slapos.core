person = context.ERP5Site_getAuthenticatedMemberPersonValue()
request = context.REQUEST
response = request.RESPONSE

certificate = url = ""
if person is None:
  response.setStatus(403)
else:
  try:
    _, url = person.signCertificate(certificate_signature_request)
    request.set('portal_status_message', context.Base_translateString('New Certificate created.'))
    certificate = person.getCertificate()
  except ValueError:
    request.set('portal_status_message', context.Base_translateString('Certificate was already requested, please revoke existing one.'))
    response.setStatus(403)
  request.set('your_certificate', certificate)
  request.set('your_certificate_url', url)

  return context.WebSection_viewCertificateAsWeb()
