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

computer = software_installation.getAggregateValue(portal_type='Computer')
if computer is None:
  return
if computer.Computer_getSoftwareReleaseUsage(url_string) != 0:
  return
if computer.getAllocationScope() not in ['open/public', 'open/subscription', 'close/forever']:
  # handle only some specific computers: public ones and removed
  return

software_installation.requestDestroy(
  comment='Destroyed by %s as %s is archived.' % (script.id, software_release.getRelativeUrl(),))
