from urlparse import urljoin, urlparse

portal = context.getPortalObject()
person = portal.portal_membership.getAuthenticatedMember().getUserValue()

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
slapos_master_web_url = portal.portal_preferences.getPreferredHateoasUrl(web_site.absolute_url())
if slapos_master_web_url is None:
  return context.Base_redirect(
    keep_items={
      'portal_status_message': 'slapos_master_web_url is not configured',
      'portal_status_level': 'error'
    }
  )

# XXX this url is HARDCODED on the client side
# and so, can not be modified
# ensure the url is relative to the web site, but without containing a //
request_url = urljoin(urljoin(slapos_master_web_url,
                              urlparse(slapos_master_web_url + '/').path.replace('//','/')),
                      "Person_requestComputer")
person.requestToken(request_url=request_url)
access_token_id = context.REQUEST.get("token")

# person.requestToken can NOT be used, as we must store
# somewhere the project reference information (that's how compatibility with existing client is done)
# so, a new token's portal type has been created for this purpose
# See Person_requestComputer script
access_token = portal.access_token_module.newContent(
  portal_type="One Time Virtual Master Access Token",
  agent_value=person,
  follow_up_value=context,
  url_string=request_url,
  # XXX this method is HARDCODED on the client side
  url_method="POST"
)
access_token_id = access_token.getId()
access_token.validate()

compute_node_install_command_line = web_site.getLayoutProperty(
  "configuration_compute_node_install_command_line",
  "wget https://deploy.erp5.net/slapos ; bash slapos")

return context.Base_renderForm(
  'Base_viewSlapOSComputeNodeTokenDialog',
  message='New Compute Node Token created.',
  keep_items={
    'your_access_token': access_token_id,
    'your_command_line': compute_node_install_command_line,
    'your_slapos_master_web': slapos_master_web_url,
    'your_slapos_master_api': slapos_master_api
  }
)
