compute_node = state_change['object']
portal = compute_node.getPortalObject()
compute_node.edit(
  capacity_scope='open'
)

# Keep this extra call separated to be compabible
# with interaction workflow whenever this is 
# updated.
compute_node.edit(
  allocation_scope='open'
)

portal.portal_workflow.doActionFor(compute_node, 'validate_action')
