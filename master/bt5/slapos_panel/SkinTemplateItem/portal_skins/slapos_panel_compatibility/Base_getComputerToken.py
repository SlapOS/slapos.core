# This script hardcoded inside slapgrid is fully deprecated
# as a compute node token MUST be associated to a project
# which means a project reference parameter is REQUIRED
# for now, this is not possible to do, as the client hardcode the url...

import json
context.RESPONSE.setStatus(410)
return json.dumps({'message': 'This API is no longer supported'})
# return context.compute_node_module.Base_getComputeNodeToken()

"""
import json

portal = context.getPortalObject()
person = portal.portal_membership.getAuthenticatedMember().getUserValue()

web_site = context.getWebSiteValue()
slapos_master_web_url = web_site.getLayoutProperty(
    "configuration_slapos_master_web_url",
    default=web_site.absolute_url()
  )

request_url = "%s/%s" % (slapos_master_web_url, "Person_requestComputer")

person.requestToken(request_url=request_url)
access_token_id = context.REQUEST.get("token")

slapos_master_api = web_site.getLayoutProperty(
    "configuration_slapos_master_api", "https://slap.vifib.com")

compute_node_install_command_line = web_site.getLayoutProperty(
  "configuration_compute_node_install_command_line",
  "wget https://deploy.erp5.net/slapos ; bash slapos")

request = context.REQUEST
response = request.RESPONSE
response.setHeader('Content-Type', "application/json")
return json.dumps({'access_token': access_token_id,
                   'command_line': compute_node_install_command_line,
                   'slapos_master_web': slapos_master_web_url,
                   'slapos_master_api': slapos_master_api})
"""
