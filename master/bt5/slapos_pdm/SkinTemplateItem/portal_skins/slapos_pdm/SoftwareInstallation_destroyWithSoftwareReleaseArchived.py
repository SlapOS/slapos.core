software_installation = context
url_string = software_installation.getUrlString()

if software_installation.getValidationState() != 'validated':
  return
if software_installation.getSlapState() != 'start_requested':
  return

software_release = software_installation.portal_catalog.getResultValue(
  portal_type='Software Release',
  validation_state='archived',
  url_string=url_string
)
if software_release is None:
  return

compute_node = software_installation.getAggregateValue(portal_type='Compute Node')
if compute_node is None:
  return
if compute_node.ComputeNode_getSoftwareReleaseUsage(url_string) != 0:
  return

if compute_node.getUpgradeScope() != 'auto':
  # handle only Compute Nodes with automatic software management
  return

software_installation.requestDestroy(
  comment='Destroyed by %s as %s is archived.' % (script.id, software_release.getRelativeUrl(),))
