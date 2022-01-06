from Products.ERP5Type.Message import translateString
from ZTUtils import make_query

portal = context.getPortalObject()

assert key
mail_message = portal.ERP5Site_unrestrictedSearchMessage(key=key)

web_site = context.getWebSiteValue()
came_from = web_site.absolute_url() + "/#!login?p.page=%s{&n.me}" % web_site.getLayoutProperty("configuration_frontpage_gadget_url")
credential_request = mail_message.getFollowUpValue()
if credential_request.getValidationState() in ('submitted', 'accepted'):
  message = translateString("Your account is already active.")
else:
  credential_request.submit(comment=translateString('Created by subscription form'))
  mail_message.deliver()
  message = translateString("Your account is being activated. You will receive an e-mail when activation is complete.")

url = "%s/login_form?portal_status_message=%s&%s" % (
  context.getWebSectionValue().absolute_url(),
  message,
  make_query({"came_from": came_from})
)

context.REQUEST.RESPONSE.setHeader('Location', url)
context.REQUEST.RESPONSE.setStatus(303)
