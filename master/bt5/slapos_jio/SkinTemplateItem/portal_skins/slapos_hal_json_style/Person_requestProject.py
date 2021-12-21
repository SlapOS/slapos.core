import json
portal = context.getPortalObject()
person = portal.portal_membership.getAuthenticatedMember().getUserValue()

request = context.REQUEST
response = request.RESPONSE

if person is None:
  response.setStatus(403)
else:
  request_kw = dict(project_title=title)
  person.requestProject(**request_kw)
  project_relative_url = request.get('project_relative_url')
  project_reference = request.get('project_reference')

  response.setHeader('Content-Type', "application/json")
  return json.dumps({
    "reference": project_reference,
    "relative_url": project_relative_url
  })
