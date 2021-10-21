#
# XXX This ticket contains dupplicated coded found arround SlapOS
#     It is required to rewrite this in a generic way. 
#     See also: InstanceTree_checkSoftwareInstanceState
#     See also: ComputeNode_checkState
#

from DateTime import DateTime
import json

if context.getSimulationState() == "invalidated":
  return "Closed Ticket"

document = context.getAggregateValue()

if document is None:
  return True


aggregate_portal_type = document.getPortalType()
memcached_dict = context.Base_getSlapToolMemcachedDict()

if aggregate_portal_type == "Compute Node":
  if document.getMonitorScope() == "disabled":
    return "Monitor is disabled to the related %s." % document.getPortalType()
  try:
    d = memcached_dict[document.getReference()]
    d = json.loads(d)
    last_contact = DateTime(d.get('created_at'))
    if (DateTime() - last_contact) < 0.01:
      return "All OK, latest contact: %s " % last_contact
    else:
      return "Problem, latest contact: %s" % last_contact
  except KeyError:
    return "No Contact Information"

if aggregate_portal_type == "Software Installation":
  compute_node_title = document.getAggregateTitle()
  if document.getAggregateValue().getMonitorScope() == "disabled":
    return "Monitor is disabled to the related %s." % document.getPortalType()

  if document.getSlapState() not in ["start_requested", "stop_requested"]:
    return "Software Installation is Destroyed."

  try:
    d = memcached_dict[document.getReference()]
    d = json.loads(d)
    last_contact = DateTime(d.get('created_at'))
    if d.get("text").startswith("building"):
      return "The software release %s is building for mode them 12 hours on %s, started on %s" % \
              (document.getUrlString(), compute_node_title, document.getCreationDate())
    elif d.get("text").startswith("#access"):
      return "All OK, software built."
    elif d.get("text").startswith("#error"):
      return "The software release %s is failing to build for too long on %s, started on %s" % \
        (document.getUrlString(), compute_node_title, document.getCreationDate())

  except KeyError:
    return "The software release %s did not started to build on %s since %s" % \
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
          compute_node.getAllocationScope() in ["open/public", "open/subscription"] and \
          instance.getSlapState() == "start_requested" and \
          instance.SoftwareInstance_hasReportedError():
        message_list.append("%s has error (%s, %s at %s scope %s)" % (instance.getReference(), instance.getTitle(),
                                                                      instance.getUrlString(), compute_node.getReference(),
                                                                      compute_node.getAllocationScope()))
      if instance.getPortalType() == "Software Instance" and \
          compute_node.getAllocationScope() in ["closed/outdated", "open/personal"] and \
          instance.getSlapState() == "start_requested" and \
          instance.SoftwareInstance_hasReportedError():
        message_list.append("%s on a %s compute_node" % (instance.getReference(), compute_node.getAllocationScope()) )
    else:
      message_list.append("%s is not allocated" % instance.getReference())
  return ",".join(message_list)

return None
