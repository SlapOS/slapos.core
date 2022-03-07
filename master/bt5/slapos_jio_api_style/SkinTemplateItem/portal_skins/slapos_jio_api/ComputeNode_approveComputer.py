import json
portal = context.getPortalObject()
person = portal.portal_membership.getAuthenticatedMember().getUserValue()

request = context.REQUEST
response = request.RESPONSE

if person is None:
  response.setStatus(403)
else:
  compute_node = context
  compute_node.generateCertificate()
  compute_node.approveComputeNodeRegistration()
  response.setHeader('Content-Type', "application/json")
  return json.dumps({
    "certificate" : request.get('compute_node_certificate'),
    "key" : request.get('compute_node_key'),
    "reference": compute_node.getReference(),
    "relative_url": compute_node.getRelativeUrl()
  })
