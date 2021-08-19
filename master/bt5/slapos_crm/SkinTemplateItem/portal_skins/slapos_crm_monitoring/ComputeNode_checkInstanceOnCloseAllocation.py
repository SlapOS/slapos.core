from Products.CMFActivity.ActiveResult import ActiveResult

portal = context.getPortalObject()
active_process = portal.restrictedTraverse(active_process)


partition_uid_list = [compute_partition.getUid() for compute_partition in context.objectValues(portal_type="Compute Partition")]

if not partition_uid_list:
  return

for software_instance in portal.portal_catalog(
    portal_type="Software Instance",
    default_aggregate_uid=partition_uid_list):
  if software_instance.getSlapState() == "destroy_requested":
    continue
  active_process.postResult(ActiveResult(
         summary="%s" % software_instance.getRelativeUrl(),
         severity=100,
         detail="%s on %s" % (software_instance.getRelativeUrl(), context.getRelativeUrl())))
