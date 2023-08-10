portal = context.getPortalObject()
person = portal.portal_membership.getAuthenticatedMember().getUserValue()

request = context.REQUEST
response = request.RESPONSE

import json

if person is None:
  response.setStatus(403)
  return {}

try:
  return json.dumps(person.generateCertificate())
  # Certificate is Created
except ValueError:
  # Certificate was already requested, please revoke existing one.
  return json.dumps(False)
