import json
portal = context.getPortalObject()
person = portal.portal_membership.getAuthenticatedMember().getUserValue()

request = context.REQUEST
response = request.RESPONSE

if person is None:
  response.setStatus(403)
else:
  request_kw = {"support_request_title": title,
                "support_request_description": description,
                "support_request_resource": resource}
  person.requestSupport(**request_kw)
  support_relative_url = request.get('support_request_relative_url')

  response.setHeader('Content-Type', "application/json")
  return json.dumps({
    "relative_url": support_relative_url
  })
