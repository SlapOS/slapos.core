# This script is hardcoded inside slapgrid
# it must only be called with an access token which provide the project to use
# See Project_addSlapOSComputeNodeToken

import json
portal = context.getPortalObject()
person = portal.portal_membership.getAuthenticatedMember().getUserValue()

request = context.REQUEST
response = request.RESPONSE

if person is None:
  response.setStatus(403)
else:
  person.requestComputeNode(
    # use a really customer key to prevent any conflict
    project_reference=context.REQUEST.get("OneTimeVirtualMasterAccessToken_getProjectReference", None),
    compute_node_title=title
  )
  compute_node = context.restrictedTraverse(context.REQUEST.get('compute_node'))
  compute_node.generateCertificate()

  response.setHeader('Content-Type', "application/json")
  return json.dumps({
    "certificate" : request.get('compute_node_certificate'),
    "key" : request.get('compute_node_key'),
    "reference": compute_node.getReference(),
    "relative_url": compute_node.getRelativeUrl()
  })
