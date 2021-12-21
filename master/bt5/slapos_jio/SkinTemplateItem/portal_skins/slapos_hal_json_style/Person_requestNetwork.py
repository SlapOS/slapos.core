import json
portal = context.getPortalObject()
person = portal.portal_membership.getAuthenticatedMember().getUserValue()

request = context.REQUEST
response = request.RESPONSE

if person is None:
  response.setStatus(403)
else:
  request_kw = dict(network_title=title)
  person.requestNetwork(**request_kw)
  network_relative_url = request.get('computer_network_relative_url')
  network_reference = request.get('computer_network_reference')

  response.setHeader('Content-Type', "application/json")
  return json.dumps({
    "reference": network_reference,
    "relative_url": network_relative_url
  })
