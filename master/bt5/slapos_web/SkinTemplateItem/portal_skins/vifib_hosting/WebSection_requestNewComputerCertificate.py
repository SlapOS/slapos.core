computer = context
request = context.REQUEST
try:
  computer.generateCertificate(csr=certificate_signature_request)
  request.set('portal_status_message', context.Base_translateString('Certificate created.'))
except ValueError:
  request.set('portal_status_message', context.Base_translateString('Certificate is still active, please revoke existing one.'))
request.set('your_certificate', request.get('computer_certificate'))
request.set('your_certificate_url', request.get('certificate_url'))

return context.Computer_viewConnectionInformationAsWeb()
