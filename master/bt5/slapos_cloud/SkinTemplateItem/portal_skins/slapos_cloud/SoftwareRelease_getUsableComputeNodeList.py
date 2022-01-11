portal = context.getPortalObject()

compute_partition_list = portal.portal_catalog(
  software_release_url=context.getUrlString(),
  free_for_request=1,
  follow_up__uid=context.getFollowUpUid(),
  group_by=("parent_uid",)
)

return [c.getParentValue() for c in compute_partition_list]
