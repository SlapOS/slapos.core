"""
  The method changeUserPassword ignore came_from if you are in the Web Site context.
"""
REQUEST = context.REQUEST
error_list = context.portal_password.analyzePassword(
  REQUEST['password'], REQUEST['password_key']
)

if error_list:
  error_message = context.Base_translateString("Password don't comply with policy: ")
  error_message += ", ".join([context.Base_translateString(i.message) for i in error_list])
  return REQUEST.RESPONSE.redirect(
    "%s/WebSite_viewResetPassword?reset_key=%s&portal_status_message=%s" % \
    (REQUEST["came_from"], REQUEST['password_key'], error_message))


next_url = context.portal_password.changeUserPassword(password=REQUEST['password'],
                                                      password_confirmation=REQUEST['password_confirm'],
                                                      password_key=REQUEST['password_key'],
                                                      user_login=REQUEST.get('user_login', None),
                                                      REQUEST=REQUEST)
root_url = "%s/" % context.getWebSiteValue().absolute_url()
return REQUEST.RESPONSE.redirect("%s&came_from=%s" % (next_url, root_url))
