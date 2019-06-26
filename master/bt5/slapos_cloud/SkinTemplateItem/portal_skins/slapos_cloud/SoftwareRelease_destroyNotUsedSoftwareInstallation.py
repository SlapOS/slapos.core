from Products.CMFActivity.ActiveResult import ActiveResult
script.log(active_process)
software_release = context
if software_release.getValidationState() != 'archived':
  return

url_string = software_release.getUrlString()
software_installation_list = software_release.portal_catalog(
  portal_type='Software Installation',
  validation_state='validated',
  url_string=url_string
)
destroyed_software_installation_list = []
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
  destroyed_software_installation_list.append(software_installation.getRelativeUrl())

if len(destroyed_software_installation_list) == 0:
  detail = "Nothing destroyed."
else:
  detail = "Destroyed %s" % ', '.join(destroyed_software_installation_list)
if active_process is not None:
  active_process_document = software_release.restrictedTraverse(active_process)
  active_process_document.activate(activity='SQLQueue').postResult(ActiveResult(
    summary="%s" % software_release.getRelativeUrl(),
    severity=0,
    detail=detail)
  )
