hosting_subscription = context.getAggregateValue()
portal = context.getPortalObject()

software_instance_list = portal.portal_catalog(
  portal_type=["Software Instance", "Slave Instance"],
  specialise_uid=hosting_subscription.getUid())

# Check if at least one software Instance is Allocated
for instance in software_instance_list:
  if instance.getSlapState() != "start_requested":
    # There is something wrong.
    return False

  computer_partition = instance.getAggregateValue()
  if computer_partition is None:
    return False

  if instance.getPortalType() == "Software Instance" and \
      instance.SoftwareInstance_hasReportedError():
    return False
 
return True
