portal = context.getPortalObject()
person = portal.portal_membership.getAuthenticatedMember().getUserValue()
web_site = context.getWebSiteValue()

if person is None:
  raise ValueError("User Not Found")

if web_site is None:
  raise ValueError("Web Site not Found")

# We expect to fail if it is not call on proper website.
request_url =  web_site.feed.absolute_url()

# XXX - Cannot search in catalog with parameter url_string
access_token = None
for token_item in portal.portal_catalog(
  portal_type="Restricted Access Token",
  default_agent_uid=person.getUid(),
  validation_state='validated'
  ):
  if token_item.getUrlString() == request_url:
    access_token = token_item
    reference = access_token.getReference()
    break

if access_token is None:
  access_token = portal.access_token_module.newContent(
    portal_type="Restricted Access Token",
    url_string=request_url,
    url_method="GET",
  )
  access_token.setAgentValue(person)
  reference = access_token.getReference()
  access_token.validate()

return "%s?access_token=%s&access_token_secret=%s" % (
        request_url,
        access_token.getId(),
        reference)
