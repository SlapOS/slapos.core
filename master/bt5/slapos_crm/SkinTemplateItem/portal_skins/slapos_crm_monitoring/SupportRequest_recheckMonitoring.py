from DateTime import DateTime

if context.getSimulationState() == "invalidated":
  return "Closed Ticket"

if context.getPortalType() != "Support Request":
  return "Not a Support Request"

now = DateTime()
portal = context.getPortalObject()
document = context.getAggregateValue()
if document is None:
  return True

aggregate_portal_type = document.getPortalType()
if aggregate_portal_type == "Compute Node":
  if document.getMonitorScope() == "disabled":
    return "Monitor is disabled to the related %s." % document.getPortalType()

  d = document.getAccessStatus()
  if d.get("no_data", None) == 1:
    return "No Contact Information"

  last_contact = DateTime(d.get('created_at'))
  if (now - last_contact) < 0.01:
    ComputeNode_hasModifiedFile = getattr(
      document, "ComputeNode_hasModifiedFile", None)
    if ComputeNode_hasModifiedFile:
      data_array  = ComputeNode_hasModifiedFile()
      if data_array:
        return "Compute Node %s (%s) has modified file: %s" % (
           document.getTitle(), document.getReference(), data_array.getReference())
    # If server has no partitions skip
    compute_partition_uid_list = [
      x.getUid() for x in document.contentValues(portal_type="Compute Partition")
      if x.getSlapState() == 'busy']

    if compute_partition_uid_list:
      is_instance_stalled = True
      last_contact = None
      instance_list = portal.portal_catalog(
        portal_type='Software Instance',
        default_aggregate_uid=compute_partition_uid_list)

      for instance in instance_list:
        instance_access_status = instance.getAccessStatus()
        if instance_access_status.get('no_data', None):
          # Ignore if there isnt any data
          continue

        # At lest one partition contacted in the last 24h30min.
        last_contact = max(DateTime(instance_access_status.get('created_at')), last_contact)
        if (now - DateTime(instance_access_status.get('created_at'))) < 1.05:
          is_instance_stalled = False
          break

      if is_instance_stalled and len(instance_list):
        if last_contact is None:
          return "Process instance stalled"
        return "Process instance stalled, last contact was %s" % last_contact

    return "All OK, latest contact: %s " % last_contact
  else:
    return "Problem, latest contact: %s" % last_contact

if aggregate_portal_type == "Software Installation":
  compute_node_title = document.getAggregateTitle()
  if document.getAggregateValue().getMonitorScope() == "disabled":
    return "Monitor is disabled to the related %s." % document.getPortalType()

  if document.getSlapState() not in ["start_requested", "stop_requested"]:
    return "Software Installation is Destroyed."

  d = document.getAccessStatus()
  if d.get("no_data", None) == 1:
    return "The software release %s did not started to build on %s since %s" % \
        (document.getUrlString(), compute_node_title, document.getCreationDate())

  last_contact = DateTime(d.get('created_at'))
  if d.get("text").startswith("building"):
    return "The software release %s is building for mode them 12 hours on %s, started on %s" % \
            (document.getUrlString(), compute_node_title, document.getCreationDate())
  elif d.get("text").startswith("#access"):
    return "All OK, software built."
  elif d.get("text").startswith("#error"):
    return "The software release %s is failing to build for too long on %s, started on %s" % \
      (document.getUrlString(), compute_node_title, document.getCreationDate())

if aggregate_portal_type == "Instance Tree":
  if document.getMonitorScope() == "disabled":
    return "Monitor is disabled to the related %s." % document.getPortalType()

  message_list = []
  instance_tree = document

  software_instance_list = instance_tree.getSpecialiseRelatedValueList(
                 portal_type=["Software Instance", "Slave Instance"])

  # Check if at least one software Instance is Allocated
  for instance in software_instance_list:
    if instance.getSlapState() not in ["start_requested", "stop_requested"]:
      continue

    if instance.getAggregate() is not None:
      compute_node = instance.getAggregateValue().getParentValue()
      if instance.getPortalType() == "Software Instance" and \
          instance.getSlapState() == "start_requested" and \
          instance.SoftwareInstance_hasReportedError():
        message_list.append("%s has error (%s, %s at %s scope %s)" % (instance.getReference(), instance.getTitle(),
                                                                      instance.getUrlString(), compute_node.getReference(),
                                                                      compute_node.getAllocationScope()))
    else:
      message_list.append("%s is not allocated" % instance.getReference())
  return ",".join(message_list)

return None
