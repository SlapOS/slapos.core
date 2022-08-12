from Products.ERP5Type.Message import translateString

compute_node = context
portal = context.getPortalObject()

compute_node.requestSoftwareRelease(
  software_release_url=url_string,
  state='available'
)

software_installation = portal.restrictedTraverse(context.REQUEST.get('software_installation_url'))
return software_installation.Base_redirect(
  keep_items={
    'portal_status_message': translateString('New Software Installation created.')
  })
