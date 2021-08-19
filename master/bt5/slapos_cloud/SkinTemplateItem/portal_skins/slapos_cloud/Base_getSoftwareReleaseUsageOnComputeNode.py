current = context.REQUEST.get('here')
if current.getPortalType() == 'Software Release':  
  software_release = current
  compute_node = context
else:
  compute_node = current
  software_release = context

return compute_node.ComputeNode_getSoftwareReleaseUsage(software_release.getUrlString())
