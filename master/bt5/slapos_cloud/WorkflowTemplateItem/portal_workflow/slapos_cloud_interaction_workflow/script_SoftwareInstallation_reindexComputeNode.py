installation = state_change['object']
compute_node = installation.getAggregateValue(portal_type=["Remote Node", "Compute Node"])
if compute_node is not None:
  compute_node.activate(
    after_path_and_method_id=(installation.getPath(), ('immediateReindexObject', 'recursiveImmediateReindexObject'))).reindexObject()
