compute_node = context.REQUEST.get('here')
software_release = context

return compute_node.ComputeNode_getSoftwareReleaseState(software_release.getUid())
