instance = state_change['object']

if instance.getSlapState() != 'stop_requested':
  portal_type = instance.getPortalType()
  if portal_type in ["Software Instance", "Slave Instance"]:
    instance.bang(
      bang_tree=False,
      comment="State changed from %s to stop_requested" % instance.getSlapState())

  if portal_type == "Slave Instance":
    partition = instance.getAggregateValue()
    if partition is not None:
      software_instance = partition.getAggregateRelatedValue(portal_type="Software Instance")
      if software_instance is not None:
        software_instance.bang(bang_tree=False,
          comment="State changed from %s (shared) to stop_requested" % instance.getSlapState())
