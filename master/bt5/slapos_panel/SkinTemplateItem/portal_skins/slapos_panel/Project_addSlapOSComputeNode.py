portal = context.getPortalObject()
person = portal.portal_membership.getAuthenticatedMember().getUserValue()

request = context.REQUEST

# XXX This API does not require to access the current user
# as no link is created between the computer and the person
person.requestComputeNode(
  compute_node_title=title,
  project_reference=context.getReference()
)
compute_node = context.restrictedTraverse(context.REQUEST.get('compute_node'))
compute_node.generateCertificate()

return context.Base_renderForm(
  'Base_viewSlapOSComputeNodeCertificateDialog',
  message='New Compute Node created.',
  keep_items={
    'your_compute_node_certificate': request.get('compute_node_certificate'),
    'your_compute_node_key': request.get('compute_node_key'),
    'your_compute_node_reference': compute_node.getReference(),
    'your_compute_node_relative_url': compute_node.getRelativeUrl()
  }
)
