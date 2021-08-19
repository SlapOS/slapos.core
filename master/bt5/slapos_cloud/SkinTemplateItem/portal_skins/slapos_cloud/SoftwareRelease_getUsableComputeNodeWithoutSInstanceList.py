compute_node_list = []
for si in context.portal_catalog(url_string=context.getUrlString(),
                                 portal_type='Software Installation',
                                 validation_state='validated'):
  compute_node = si.getAggregateValue()
  if si.getSlapState() == 'start_requested' and \
      not compute_node.ComputeNode_getSoftwareReleaseUsage(context.getUrlString()) \
      and compute_node.getValidationState() == 'validated':
    compute_node_list.append(compute_node)

return compute_node_list
