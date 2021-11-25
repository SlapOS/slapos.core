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
  project = context.restrictedTraverse(context.REQUEST.get('project'))

  return json.dumps({
    "reference": project.getReference(),
    "relative_url": project.getRelativeUrl()
  })
