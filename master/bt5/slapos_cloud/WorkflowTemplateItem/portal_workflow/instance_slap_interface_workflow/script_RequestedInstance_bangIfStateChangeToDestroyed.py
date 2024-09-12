instance = state_change['object']

if instance.getSlapState() != 'destroy_requested':
  portal_type = instance.getPortalType()
  if portal_type in ["Software Instance", "Slave Instance"]:
    instance.bang(
      bang_tree=False,
      comment="State changed from %s to destroy_requested" % instance.getSlapState())

  if portal_type == "Slave Instance":
    partition = instance.getAggregateValue()
    if partition is not None:
      software_instance = partition.getAggregateRelatedValue(portal_type="Software Instance")
      if software_instance is not None:
        software_instance.SoftwareInstance_bangAsSelf(
          relative_url=software_instance.getRelativeUrl(),
          reference=software_instance.getReference(),
          bang_tree=False,
          comment="State changed from %s (shared) to destroy_requested" % instance.getSlapState()
        )
