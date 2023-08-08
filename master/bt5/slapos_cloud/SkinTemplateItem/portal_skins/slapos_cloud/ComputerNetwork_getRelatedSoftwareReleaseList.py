portal = context.getPortalObject()
url_string_list = []
for software_installation in portal.portal_catalog(
  portal_type='Software Installation',
  validation_state='validated',
  default_aggregate_uid=[
    x.uid for x in context.portal_catalog(
      default_subordination_uid=context.getUid(),
      portal_type="Compute Node")]
):
  if software_installation.getSlapState() == 'start_requested':
    url_string = software_installation.getUrlString()
    if url_string:
      url_string_list.append(url_string)

if url_string_list:
  return context.portal_catalog(
    portal_type="Software Release",
    url_string=url_string_list)
else:
  return []
