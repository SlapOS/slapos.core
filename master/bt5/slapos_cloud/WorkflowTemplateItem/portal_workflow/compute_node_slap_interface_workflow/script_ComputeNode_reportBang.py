compute_node = state_change['object']
portal = compute_node.getPortalObject()
for compute_partition in [x for x in compute_node.contentValues(portal_type='Compute Partition') if x.getSlapState() == 'busy']:
  for instance_sql in portal.portal_catalog(
                        default_aggregate_uid=compute_partition.getUid(),
                        portal_type=["Software Instance", "Slave Instance"],
                        ):
    instance = instance_sql.getObject()
    if instance.getSlapState() in ["start_requested", "stop_requested"]:
      instance.activate().SoftwareInstance_bangAsSelf(
        relative_url=instance.getRelativeUrl(),
        reference=instance.getReference(), 
        comment=state_change.kwargs.get('comment', ''))

compute_node.setErrorStatus('bang')
