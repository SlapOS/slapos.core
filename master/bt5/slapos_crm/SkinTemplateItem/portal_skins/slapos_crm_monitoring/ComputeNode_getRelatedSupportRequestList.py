portal = context.getPortalObject()

uid_list = [context.getUid()]
for instance in portal.portal_catalog(
    portal_type="Software Instance",
    default_aggregate_uid=[cp.uid for cp in context.searchFolder(portal_type="Compute Partition")]):
  uid_list.append(instance.getSpecialiseUid(portal_type="Instance Tree"))

return portal.portal_catalog(
  portal_type='Support Request',
  default_aggregate_uid=uid_list,
  **kw)
