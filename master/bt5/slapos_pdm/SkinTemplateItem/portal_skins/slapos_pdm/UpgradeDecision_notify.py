from DateTime import DateTime
return
if context.getSimulationState() != 'planned':
  # XXX Don't notify the ones which are not planned.
  return 

portal = context.getPortalObject()

person = context.getDestinationDecisionValue(portal_type="Person")
if not person:
  raise ValueError("Inconsistent Upgrade Decision, No Destination Decision")

instance_tree = context.UpgradeDecision_getAggregateValue("Instance Tree")
compute_node = context.UpgradeDecision_getAggregateValue("Compute Node")
software_release = context.UpgradeDecision_getSoftwareRelease()
software_product_title = software_release.getAggregateTitle(
                               portal_type="Software Product")

mapping_dict = {
  'software_product_title': software_product_title,
  'software_release_name': software_release.getTitle(),
  'software_release_reference': software_release.getReference(),
  'new_software_release_url': software_release.getUrlString(),

}
if instance_tree is not None:
  notification_message_reference = 'slapos-upgrade-instance-tree.notification'
  title = "New Upgrade available for %s" % instance_tree.getTitle()
  mapping_dict.update(**{
     'instance_tree_title': instance_tree.getTitle(),
     'old_software_release_url': instance_tree.getUrlString()})


elif compute_node is not None:

  notification_message_reference = 'slapos-upgrade-compute-node.notification' 

  title = "New Software available for Installation at %s" % compute_node.getTitle()
  mapping_dict.update(**{'compute_node_title': compute_node.getTitle(),
                         'compute_node_reference': compute_node.getReference()})


if notification_message_reference is None:
  raise ValueError("No Notification Message")

notification_message = portal.portal_notifications.getDocumentValue(
                 reference=notification_message_reference)

message = notification_message.asEntireHTML(
            substitution_method_parameter_dict={'mapping_dict': mapping_dict})

event = context.SupportRequest_trySendNotificationMessage(title,
              message, person.getRelativeUrl())

if event is not None:
  context.confirm()
