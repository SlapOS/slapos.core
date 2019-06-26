return_list = []
PROTECTED_SOFTWARE_RELEASE_URL_LIST = [
  'http://git.erp5.org/gitweb/slapos.git/blob_plain/HEAD:/software/apache-frontend/software.cfg'
]
for sr in context.portal_catalog(*args, **kwargs):
  if sr.Base_getSoftwareReleaseUsageOnComputer() != 0:
    continue
  if sr.Base_getSoftwareReleaseStateOnComputer() != 'Installation requested':
    continue
  if sr.getUrlString() in PROTECTED_SOFTWARE_RELEASE_URL_LIST:
    continue
  return_list.append(sr)
return return_list
