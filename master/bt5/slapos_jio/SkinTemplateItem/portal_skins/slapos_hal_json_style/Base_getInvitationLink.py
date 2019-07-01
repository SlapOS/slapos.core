import json
from zExceptions import Unauthorized 

portal = context.getPortalObject()
person = portal.portal_membership.getAuthenticatedMember().getUserValue()

if context.getPortalType() != "Organisation":
  raise Unauthorized

web_site = context.getWebSiteValue()
request_method = "POST"

request_url = "%s/%s/%s" % (web_site.absolute_url(), context.getRelativeUrl(), "Organisation_acceptInvitation")

# Maybe it would be better to use another portal_type 
access_token = portal.invitation_token_module.newContent(
  portal_type="Invitation Token",
  source_value=person,
  url_string=request_url,
  url_method=request_method
)
access_token.validate()

request = context.REQUEST
response = request.RESPONSE
response.setHeader('Content-Type', "application/json")
return json.dumps({'invitation_link': "%s?invitation_token=%s" % (request_url, access_token.getId())})
