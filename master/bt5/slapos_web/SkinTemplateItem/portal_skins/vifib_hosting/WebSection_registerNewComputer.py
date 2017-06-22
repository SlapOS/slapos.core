"""
  If certificate_request is None will only create the computer without 
  generate a certificate.
"""

portal = context.getPortalObject()
person = portal.ERP5Site_getAuthenticatedMemberPersonValue()

request = context.REQUEST
response = request.RESPONSE

if person is None:
  response.setStatus(403)
else:
  request_kw = dict(computer_title=title)
  person.requestComputer(**request_kw)
  computer = context.restrictedTraverse(context.REQUEST.get('computer'))
  if certificate_request is not None:
    computer.generateCertificate(certificate_request=certificate_request)
  message = "Registering Computer"
  context.REQUEST.set("portal_status_message", message)
  return computer.Computer_viewConnectionInformationAsWeb()
