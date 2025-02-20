compute_node = state_change['object']
portal = compute_node.getPortalObject()
compute_partition_uid_list = [x.getUid() for x in compute_node.contentValues(portal_type='Compute Partition') if x.getSlapState() == 'busy']

for instance_sql in portal.portal_catalog(
  default_aggregate_uid=compute_partition_uid_list,
  portal_type=["Software Instance", "Slave Instance"],
  validation_state='validated',
  # Try limiting conflicts on multiple instances of the same tree
  # example: monitor frontend
  group_by_list=['specialise_uid']
):
  instance = instance_sql.getObject()
  if instance.getSlapState() in ["start_requested", "stop_requested"]:
    # Increase priority to not block indexations
    # if there are many activities created
    instance.activate(priority=2).SoftwareInstance_bangAsSelf(
      relative_url=instance.getRelativeUrl(),
      reference=instance.getReference(),
      comment=state_change.kwargs.get('comment', '')
    )

compute_node.setErrorStatus('bang')
