compute_node = context.getAggregateValue(
    portal_type='Compute Node'
  )
url_string = context.getUrlString()

if compute_node.ComputeNode_getSoftwareReleaseUsage(url_string) == 0:
  message = 'Requested Destruction'
  compute_node.requestSoftwareRelease(
    software_release_url=url_string,
    state='destroyed')
else:
  message = 'This software installation is used and cannot be destroyed'

return context.Base_redirect('view', keep_items={'portal_status_message': message})
