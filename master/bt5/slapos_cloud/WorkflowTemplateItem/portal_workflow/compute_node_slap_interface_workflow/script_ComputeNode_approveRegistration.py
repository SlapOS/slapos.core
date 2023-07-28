compute_node = state_change['object']
portal = compute_node.getPortalObject()
person = portal.portal_membership.getAuthenticatedMember().getUserValue()
compute_node.edit(
  allocation_scope='open/personal',
  source_administration_value=person,
  upgrade_scope='auto',
  capacity_scope='open'
)

portal.portal_workflow.doActionFor(compute_node, 'validate_action')
