from Products.PythonScripts.standard import Object

from DateTime import DateTime

if context.getSimulationState() == "invalidated":
  return []

document = context.getAggregateValue()

if document is None:
  return []

aggregate_portal_type = document.getPortalType()

if aggregate_portal_type in ["Compute Node", "Instance Tree"] and \
  document.getMonitorScope("disabled") == "disabled":
  return []

if aggregate_portal_type == "Instance Tree":
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
        m, create_at, since = instance.SoftwareInstance_hasReportedError(include_message=True,
                                                                  include_created_at=True,
                                                                  include_since=True)
        message_list.append(Object(
            pasth=instance.getRelativeUrl(),
            uid=instance.getUid(),
            title= instance.getTitle(),
            specialise_title=instance_tree.getTitle(),
            software_release=instance.getUrlString(),
            compute_node_reference=compute_node.getReference(),
            allocation_scope=compute_node.getAllocationScope(),
            follow_up_title=context.getFollowUpTitle(),
            message=m,
            created_at=create_at,
            since=since,
            age="%s m ago" % (int((DateTime()-DateTime(since))*24*60))))
    else:
      message_list.append(Object(
          relative_url=instance.getRelativeUrl(),
          uid=instance.getUid(),
          title=instance.getTitle(),
          specialise_title=instance_tree.getTitle(),
          software_release=instance.getUrlString(),
          follow_up_title=context.getFollowUpTitle(),
          compute_node_reference="",
          allocation_scope="",
          message="Instance isn't allocated"))
  return message_list

return []
