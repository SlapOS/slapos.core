from Products.ERP5Type.Message import translateString

portal = context.getPortalObject()
person = portal.portal_membership.getAuthenticatedMember().getUserValue()

# XXX This API does not require to access the current user
# as no link is created between the computer network and the person
person.requestNetwork(
  network_title=title,
  project_reference=context.getReference()
)
compute_network = context.restrictedTraverse(context.REQUEST.get('computer_network_relative_url'))

return compute_network.Base_redirect(
  keep_items={
    'portal_status_message': translateString('New Computer Network created.')
  }
)
