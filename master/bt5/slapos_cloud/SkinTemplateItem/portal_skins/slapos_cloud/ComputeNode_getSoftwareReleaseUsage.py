portal = context.getPortalObject()
if context.getParentValue().isMemberOf('allocation_scope/open'):
  # This is faster but all values are free_for_request == 0 if the computer is closed
  return context.getPortalObject().portal_catalog.countResults(
    portal_type='Compute Partition',
    parent_uid=context.getUid(),
    free_for_request=0,
    software_release_url=software_release_url)[0][0]
else:
  computer_uid_list = [i.uid for i in portal.portal_catalog(
    portal_type='Compute Partition',
    parent_uid=context.getUid()
  )]
  if not computer_uid_list:
    return 0
  return portal.portal_catalog.countResults(
    portal_type='Software Instance',
    default_aggregate_uid=computer_uid_list,
    url_string=software_release_url)[0][0]
