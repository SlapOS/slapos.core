return context.getPortalObject().portal_catalog.countResults(
  portal_type='Computer Partition',
  parent_uid=context.getUid(),
  free_for_request=0,
  software_release_url=software_release_url
)[0][0]
