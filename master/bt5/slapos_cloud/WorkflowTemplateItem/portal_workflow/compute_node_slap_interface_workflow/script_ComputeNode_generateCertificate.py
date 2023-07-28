compute_node = state_change['object']

for certificate_login in compute_node.objectValues(
  portal_type=["Certificate Login"]):
  if certificate_login.getValidationState() == "validated":
    context.REQUEST.set("compute_node_certificate", None)
    context.REQUEST.set("compute_node_key", None)
    raise ValueError('Certificate still active.')
    
certificate_login = compute_node.newContent(
  portal_type="Certificate Login")
certificate_login.validate()

certificate_dict = certificate_login.getCertificate()

context.REQUEST.set("compute_node_certificate", certificate_dict["certificate"])
context.REQUEST.set("compute_node_key", certificate_dict["key"])
