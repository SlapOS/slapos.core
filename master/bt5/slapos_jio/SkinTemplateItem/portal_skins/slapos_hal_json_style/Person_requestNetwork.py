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
  network_relative_url = context.REQUEST.get('computer_network_relative_url')
  network_reference = context.REQUEST.get('computer_network_reference')

  return json.dumps({
    "reference": network_reference,
    "relative_url": network_relative_url
  })
