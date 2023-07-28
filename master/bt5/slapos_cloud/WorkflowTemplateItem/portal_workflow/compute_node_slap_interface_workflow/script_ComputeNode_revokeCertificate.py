compute_node = state_change['object']

context.REQUEST.set('compute_node_certificate', None)
context.REQUEST.set('compute_node_key', None)

no_certificate = True
for certificate_login in compute_node.objectValues(
  portal_type=["Certificate Login"]):
  if certificate_login.getValidationState() == "validated":
    certificate_login.invalidate()
    no_certificate = False

if no_certificate:
  raise ValueError('No certificate')
