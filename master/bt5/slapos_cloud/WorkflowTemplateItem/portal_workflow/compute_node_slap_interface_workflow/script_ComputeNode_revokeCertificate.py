compute_node = state_change['object']
context.REQUEST.set('compute_node_certificate', None)
context.REQUEST.set('compute_node_key', None)
destination_reference = compute_node.getDestinationReference()
if destination_reference is None:
  raise ValueError('No certificate')
context.getPortalObject().portal_certificate_authority.revokeCertificate(destination_reference)
compute_node.setDestinationReference(None)
