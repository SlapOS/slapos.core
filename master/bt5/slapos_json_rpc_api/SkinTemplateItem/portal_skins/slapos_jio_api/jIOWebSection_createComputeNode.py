import json
portal = context.getPortalObject()
person = portal.portal_membership.getAuthenticatedMember().getUserValue()

request = context.REQUEST
response = request.RESPONSE

if person is None:
  response.setStatus(403)
  return

request_kw = dict(
  compute_node_title=data_dict.get("title", None),
  approve_registration=approve_registration,
)
person.requestComputeNode(**request_kw)
compute_node = context.restrictedTraverse(context.REQUEST.get('compute_node'))

web_site = context.getWebSiteValue()
slapos_master_web_url = web_site.getLayoutProperty(
  "configuration_slapos_master_web_url",
  default=web_site.absolute_url()
)

request_url = "%s/%s" % (slapos_master_web_url.strip("/"), "%s/ComputeNode_approveComputer" % compute_node.getRelativeUrl())

person.requestToken(request_url=request_url)
access_token_id = context.REQUEST.get("token")

slapos_master_api = web_site.getLayoutProperty(
    "configuration_slapos_master_api", "https://slap.vifib.com")

compute_node_install_command_line = web_site.getLayoutProperty(
  "configuration_compute_node_install_command_line",
  "wget https://deploy.erp5.net/slapos ; bash slapos")

response.setHeader('Content-Type', "application/json")
return json.dumps({
  "$schema": context.getPortalObject().portal_types.restrictedTraverse(compute_node.getPortalType()).absolute_url()
    + "/getTextContent",
  "compute_node_id" : compute_node.getReference(),
  "access_token": "V2/" + compute_node.getId() + "/" + access_token_id,
  "certificate_url_access": request_url,
  "initialisation_comand": compute_node_install_command_line,
  "slapos_master_web": slapos_master_web_url,
  "slapos_master_api": slapos_master_api,
  # Kept for backward compatibility
  "command_line": compute_node_install_command_line,
}, indent=2)
