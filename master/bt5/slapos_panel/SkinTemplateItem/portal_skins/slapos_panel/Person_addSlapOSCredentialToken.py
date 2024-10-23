from urlparse import urljoin, urlparse

person = context

web_site = context.getWebSiteValue()

slapos_master_api = web_site.getLayoutProperty(
    "configuration_slapos_master_api", None)
if slapos_master_api is None:
  return context.Base_redirect(
    keep_items={
      'portal_status_message': 'configuration_slapos_master_api is not configured',
      'portal_status_level': 'error'
    }
  )

# This url is only used to call 1 (one) python script.
# it could be whatever url able to reach erp5
slapos_master_web_url = web_site.absolute_url()

# XXX this url is HARDCODED on the client side
# and so, can not be modified
# ensure the url is relative to the web site, but without containing a //
request_url = urljoin(urljoin(slapos_master_web_url,
                              urlparse(slapos_master_web_url + '/').path.replace('//','/')),
                      "Person_getCertificate")
person.requestToken(request_url=request_url)
access_token_id = context.REQUEST.get("token")

return context.Base_renderForm(
  'Base_viewSlapOSComputeNodeTokenDialog',
  message='New Credential Token created.',
  keep_items={
    'your_access_token': access_token_id,
    'your_command_line': "slapos configure client",
    'your_slapos_master_web': slapos_master_web_url,
    'your_slapos_master_api': slapos_master_api
  }
)
