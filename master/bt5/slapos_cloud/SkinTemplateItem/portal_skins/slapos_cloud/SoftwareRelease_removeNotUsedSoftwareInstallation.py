software_release = context
url_string = software_release.getUrlString()
software_installation_list = software_release.portal_catalog(
  portal_type='Software Installation',
  validation_state='validated',
  url_string=url_string
)
for software_installation in software_installation_list:
  if software_installation.getSlapState() != 'start_requested':
    continue
  if software_installation.getValidationState() != 'validated':
    continue
  computer = software_installation.getAggregateValue(portal_type='Computer')
  if computer is None:
    continue
  if computer.Computer_getSoftwareReleaseUsage(url_string) != 0:
    continue
  software_installation.requestDestroy()
