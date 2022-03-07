log_error = context.ERP5Site_logApiErrorAndReturn
import json
portal = context.getPortalObject()
person = portal.portal_membership.getAuthenticatedMember().getUserValue()

request = context.REQUEST
response = request.RESPONSE

if person is None:
  response.setStatus(403)
else:
  request_kw = dict(
    compute_node_title=data_dict["title"],
    approve_registration=False,
  )
  person.requestComputeNode(**request_kw)
  compute_node = context.restrictedTraverse(context.REQUEST.get('compute_node'))

  web_site = context.getWebSiteValue()
  slapos_master_web_url = web_site.getLayoutProperty(
    "configuration_slapos_master_web_url",
    default=web_site.absolute_url()
  )

  request_url = "%s/%s" % (slapos_master_web_url, "%s/ComputeNode_approveComputer" % compute_node.getRelativeUrl())

  person.requestToken(request_url=request_url)
  access_token_id = context.REQUEST.get("token")
  response.setHeader('Content-Type', "application/json")
  return json.dumps({
    "$schema": context.getPortalObject().portal_types.restrictedTraverse(compute_node.getPortalType()).absolute_url()
      + "/getTextContent",
    "title" : compute_node.getTitle(),
    "id" : compute_node.getRelativeUrl(),
    "reference": compute_node.getReference(),
    "access_token": "V2/" + compute_node.getId() + "/" + access_token_id,
    "access_token_url": request_url,
    "modification_date": compute_node.getModificationDate().HTML4(),
  })
