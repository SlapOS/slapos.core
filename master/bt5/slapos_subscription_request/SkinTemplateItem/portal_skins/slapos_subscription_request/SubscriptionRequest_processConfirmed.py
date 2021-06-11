instance_tree = context.getAggregateValue()

if instance_tree is None:
  # Probably we should raise here
  return

# Instance is already destroyed so move into stopped state diretly.
if instance_tree.getValidationState() == "archived":
  comment="Instance Tree is Destroyed and archived, Stop the Subscription Request"
  context.start(comment=comment)
  context.stop(comment=comment)
  return comment

request_kw = dict(
      software_release=instance_tree.getUrlString(),
      software_title=instance_tree.getTitle(),
      software_type=instance_tree.getSourceReference(),
      instance_xml=instance_tree.getTextContent(),
      sla_xml=instance_tree.getSlaXml(),
      shared=instance_tree.isRootSlave()
)

if not context.SubscriptionRequest_testPaymentBalance():
  # Payment isn't paid by the user, so we stop the instance and wait
  if instance_tree.getSlapState() == "start_requested":
    person = instance_tree.getDefaultDestinationSectionValue()
    person.requestSoftwareInstance(state='stopped', **request_kw)
  return "Skipped (Payment is pending)"

if instance_tree.getSlapState() == "stop_requested":
  person = instance_tree.getDefaultDestinationSectionValue()
  person.requestSoftwareInstance(state='started', **request_kw)
  # Return to because it is useless continue right the way.
  return "Skipped (Started instance)"

if not context.SubscriptionRequest_verifyInstanceIsAllocated():
  # Only continue if instance is ready
  return "Skipped (Instance is failing)"

if context.SubscriptionRequest_notifyInstanceIsReady():
  context.start(comment="Instance is ready")
  return "Instance is ready"

return "Skipped (Instance isn't ready)"
