computer = context
assert computer.getPortalType() == 'Computer'

PROTECTED_SOFTWARE_RELEASE_URL_LIST = [
  'http://git.erp5.org/gitweb/slapos.git/blob_plain/HEAD:/software/apache-frontend/software.cfg'
]

software_url_string_to_remove_list = []

for software_installation in context.getPortalObject().portal_catalog(
  portal_type='Software Installation',
  default_aggregate_uid=computer.getUid(),
  validation_state='validated',
):
  url_string = software_installation.getUrlString()
  if software_installation.getUrlString() in PROTECTED_SOFTWARE_RELEASE_URL_LIST:
    continue
  if computer.Computer_getSoftwareReleaseUsage(url_string) > 0:
    continue
  software_url_string_to_remove_list.append(url_string)

for url_string in software_url_string_to_remove_list:
  computer.requestSoftwareRelease(software_release_url=url_string, state='destroyed')
