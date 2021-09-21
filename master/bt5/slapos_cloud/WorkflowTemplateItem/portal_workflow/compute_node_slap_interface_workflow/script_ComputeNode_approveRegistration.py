compute_node = state_change['object']
portal = compute_node.getPortalObject()
person = portal.portal_membership.getAuthenticatedMember().getUserValue()
compute_node.edit(
  allocation_scope='open/personal',
  source_administration_value=person,
)

erp5_login = compute_node.newContent(
  portal_type="Certificate Login",
  reference=compute_node.getReference()
)
erp5_login.validate()

portal.portal_workflow.doActionFor(compute_node, 'validate_action')
