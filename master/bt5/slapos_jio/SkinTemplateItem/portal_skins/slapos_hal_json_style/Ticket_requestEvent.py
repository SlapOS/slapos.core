import json
portal = context.getPortalObject()
person = portal.portal_membership.getAuthenticatedMember().getUserValue()

request = context.REQUEST
response = request.RESPONSE

if person is None:
  response.setStatus(403)
else:
  request_kw = {
    "event_title" : title,
    "event_content": text_content,
    "event_source": person.getRelativeUrl()
  }
  context.requestEvent(**request_kw)
  event_relative_url = request.get('event_relative_url')

  response.setHeader('Content-Type', "application/json")
  return json.dumps({
    "relative_url": event_relative_url
  })
