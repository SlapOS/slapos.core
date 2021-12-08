project = state_change['object']
portal = context.getPortalObject()
person = portal.portal_membership.getAuthenticatedMember().getUserValue()

request_method = "POST"
script_name = "Project_acceptInvitation"

web_site = context.getWebSiteValue()
if web_site is None:
  web_site = portal

request_url = "%s/%s/%s" % (web_site.absolute_url(), project.getRelativeUrl(), script_name)

# Maybe it would be better to use another portal_type 
token = portal.invitation_token_module.newContent(
  portal_type="Invitation Token",
  source_value=person,
  url_string=request_url,
  url_method=request_method
)
token.validate()

context.REQUEST.set('request_token_id', token.getId())
context.REQUEST.set('request_token_url_string', request_url)
