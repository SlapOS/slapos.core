import json
portal = context.getPortalObject()
person = portal.portal_membership.getAuthenticatedMember().getUserValue()

request = context.REQUEST
response = request.RESPONSE

if person is None:
  response.setStatus(403)
else:
  request_kw = dict(compute_node_title=title)
  person.requestComputeNode(**request_kw)
  compute_node = context.restrictedTraverse(context.REQUEST.get('compute_node'))
  compute_node.generateCertificate()

  return json.dumps({
    "certificate" : request.get('compute_node_certificate'),
    "key" : request.get('compute_node_key'),
    "reference": compute_node.getReference(),
    "relative_url": compute_node.getRelativeUrl()
  })
