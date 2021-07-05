instance_tree = context.getAggregateValue()
portal = context.getPortalObject()

software_instance_list = portal.portal_catalog(
  portal_type=["Software Instance", "Slave Instance"],
  specialise_uid=instance_tree.getUid())

# Check if at least one software Instance is Allocated
for instance in software_instance_list:
  # All partitions should be allocated
  if instance.getAggregate() is None:
    if verbose:
      return "%s isn't allocated" % instance.getRelativeUrl()
    return False

  if instance.getPortalType() == "Software Instance":
    if instance.getSlapState() == "start_requested" and \
      instance.SoftwareInstance_hasReportedError():
      if verbose:
        return "Instance %s has reported errors: %s" % (
           instance.getRelativeUrl(), 
           instance.SoftwareInstance_hasReportedError(
             include_message=True))
      return False

return True
