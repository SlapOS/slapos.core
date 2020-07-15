hosting_subscription = context.getAggregateValue()
portal = context.getPortalObject()

software_instance_list = portal.portal_catalog(
  portal_type=["Software Instance", "Slave Instance"],
  specialise_uid=hosting_subscription.getUid())

# Check if at least one software Instance is Allocated
for instance in software_instance_list:
  # All partitions should be allocated
  computer_partition = instance.getAggregateValue()
  if computer_partition is None:
    return False

  if instance.getPortalType() == "Software Instance":
    if instance.getSlapState() == "start_requested" and \
      instance.SoftwareInstance_hasReportedError():
      return False

return True
