import json

portal = context.getPortalObject()
person = portal.portal_membership.getAuthenticatedMember().getUserValue()

web_site = context.getWebSiteValue()
request_method = "POST"

slapos_master_web_url = web_site.getLayoutProperty(
    "configuration_slapos_master_web_url", web_site.absolute_url())

request_url = "%s/%s" % (slapos_master_web_url, "Person_requestComputer")

access_token = portal.access_token_module.newContent(
  portal_type="One Time Restricted Access Token",
  agent_value=person,
  url_string=request_url,
  url_method=request_method
)
access_token_id = access_token.getId()
access_token.validate()

slapos_master_api = web_site.getLayoutProperty(
    "configuration_slapos_master_api", "https://slap.vifib.com")

computer_install_command_line = web_site.getLayoutProperty(
  "configuration_computer_install_command_line",
  "wget https://deploy.erp5.net/slapos ; bash slapos")

request = context.REQUEST
response = request.RESPONSE
response.setHeader('Content-Type', "application/json")
return json.dumps({'access_token': access_token_id,
                   'command_line': computer_install_command_line,
                   'slapos_master_web': slapos_master_web_url,
                   'slapos_master_api': slapos_master_api})
