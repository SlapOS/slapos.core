instance = context
if instance.getSlapState() != 'destroy_requested':
  return
if instance.getValidationState() != 'invalidated':
  # Node must confirm the destruction before unallocation
  return

partition = instance.getAggregateValue(portal_type="Compute Partition")
portal = instance.getPortalObject()
if partition is not None:
  # Partition may be managed by another instance at the same time
  # Prevent creating two instances with the same title
  tag = "allocate_%s" % partition.getRelativeUrl()
  if (portal.portal_activities.countMessageWithTag(tag) == 0):
    # No concurrency issue
    instance.unallocatePartition()

    if (partition.getId() == 'SHARED_REMOTE') and (partition.getParentValue().getPortalType() == 'Remote Node'):
      # Do not free the SHARED_REMOTE partition on Remote Node
      # used to allocate Slave Instance
      # This partition is always busy, as no Software Instance is allocated on it
      return

    instance_sql_list = portal.portal_catalog(
                          portal_type=["Software Instance", "Slave Instance"],
                          aggregate__uid=partition.getUid(),
                        )
    count = len(instance_sql_list)
    if count == 0:
      # Current instance should at least be cataloggued
      pass
    else:
      can_be_free = True
      for instance_sql in instance_sql_list:
        new_instance = instance_sql.getObject()
        if new_instance.getAggregateValue(portal_type="Compute Partition") is not None:
          can_be_free = False
          break
      if can_be_free:
        if partition.getSlapState() != "free":
          partition.markFree()
