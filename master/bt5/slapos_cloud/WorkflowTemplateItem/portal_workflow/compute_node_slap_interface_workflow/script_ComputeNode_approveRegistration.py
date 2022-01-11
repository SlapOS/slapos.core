compute_node = state_change['object']
portal = compute_node.getPortalObject()
compute_node.edit(
  allocation_scope='open',
  capacity_scope='open'
)

portal.portal_workflow.doActionFor(compute_node, 'validate_action')
