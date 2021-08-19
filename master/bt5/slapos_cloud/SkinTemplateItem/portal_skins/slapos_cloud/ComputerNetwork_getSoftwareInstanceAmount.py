portal = context.getPortalObject()
software_release = context.REQUEST.get('here')

compute_node_uid_list = [x.getUid() for x in context.getSubordinationRelatedValueList()]

return portal.portal_catalog.countResults(
  portal_type='Compute Partition',
  parent_uid=compute_node_uid_list,
  free_for_request=0,
  software_release_url=software_release.getUrlString()
)[0][0]
