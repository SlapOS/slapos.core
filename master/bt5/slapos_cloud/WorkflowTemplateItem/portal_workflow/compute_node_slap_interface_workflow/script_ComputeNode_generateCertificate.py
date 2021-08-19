compute_node = state_change['object']

if compute_node.getDestinationReference() is not None:
  context.REQUEST.set("compute_node_certificate", None)
  context.REQUEST.set("compute_node_key", None)
  raise ValueError('Certificate still active.')

ca = context.getPortalObject().portal_certificate_authority
certificate_dict = ca.getNewCertificate(compute_node.getReference())

compute_node.setDestinationReference(certificate_dict["id"])

context.REQUEST.set("compute_node_certificate", certificate_dict["certificate"])
context.REQUEST.set("compute_node_key", certificate_dict["key"])
