import json

portal = context.getPortalObject()
person = portal.portal_membership.getAuthenticatedMember().getUserValue()

web_site = context.getWebSiteValue()
request_url = "%s/%s" % (
  web_site.getLayoutProperty(
    "configuration_slapos_master_web_url",
    default=web_site.absolute_url()
  ),
  "Person_getCertificate"
)

person.requestToken(request_url=request_url)
access_token_id = context.REQUEST.get("token")

request = context.REQUEST
response = request.RESPONSE
response.setHeader('Content-Type', "application/json")
return json.dumps({'access_token': access_token_id,
                   'command_line': "slapos configure client"})
