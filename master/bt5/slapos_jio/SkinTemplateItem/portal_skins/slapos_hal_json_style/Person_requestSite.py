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
  organisation_relative_url = context.REQUEST.get('organisation_relative_url')
  organisation_reference = context.REQUEST.get('organisation_reference')

  return json.dumps({
    "reference": organisation_reference,
    "relative_url": organisation_relative_url
  })
