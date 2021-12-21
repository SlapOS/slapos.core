import json
portal = context.getPortalObject()
person = portal.portal_membership.getAuthenticatedMember().getUserValue()

request = context.REQUEST
response = request.RESPONSE

if person is None:
  response.setStatus(403)
else:
  request_kw = dict(organisation_title=title)
  person.requestSite(**request_kw)
  organisation_relative_url = request.get('organisation_relative_url')
  organisation_reference = request.get('organisation_reference')

  response.setHeader('Content-Type', "application/json")
  return json.dumps({
    "reference": organisation_reference,
    "relative_url": organisation_relative_url
  })
