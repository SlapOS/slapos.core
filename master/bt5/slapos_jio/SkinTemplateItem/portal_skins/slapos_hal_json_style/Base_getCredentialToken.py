import json

portal = context.getPortalObject()
person = portal.portal_membership.getAuthenticatedMember().getUserValue()

# Revoke user certificate
try:
  person.revokeCertificate()
except ValueError:
  pass

web_site = context.getWebSiteValue()
request_method = "POST"

request_url = "%s/%s" % (web_site.absolute_url(), "Person_getCertificate")

access_token = portal.access_token_module.newContent(
  portal_type="One Time Restricted Access Token",
  agent_value=person,
  url_string=request_url,
  url_method=request_method
)
access_token.validate()

request = context.REQUEST
response = request.RESPONSE
response.setHeader('Content-Type', "application/json")
return json.dumps({'access_token': access_token.getId(),
                   'command_line': "slapos configure client"})
