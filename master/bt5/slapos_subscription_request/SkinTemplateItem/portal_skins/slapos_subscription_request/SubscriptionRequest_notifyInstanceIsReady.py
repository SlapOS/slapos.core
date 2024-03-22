portal = context.getPortalObject()

if context.getSimulationState() != "confirmed":
  return

instance_tree = context.getAggregateValue()

for instance in instance_tree.getSpecialiseRelatedValueList(portal_type="Software Instance"):
  if (not instance.getAggregate()) or instance.SoftwareInstance_hasReportedError():
    # Some instance still failing, so instance seems not ready yet.
    return

# Instance is ok, we should move foward
portal = context.getPortalObject()
sender = context.getSourceSectionValue(portal_type="Person")
recipient = context.getDestinationSectionValue(portal_type="Person")

language = context.getLanguage(recipient.getLanguage())

# Get message from catalog
notification_reference = 'subscription_request-instance-is-ready'
notification_message = portal.portal_notifications.getDocumentValue(
    reference=notification_reference, language=language)

if notification_message is None:
  raise ValueError('Unable to found Notification Message with reference "%s".' % notification_reference)

# Set notification mapping
notification_mapping_dict = {
  'name': recipient.getTitle(),
  'subscription_title': context.getTitle(),
  'instance_tree_relative_url': instance_tree.getRelativeUrl()}

# Preserve HTML else convert to text
if notification_message.getContentType() == "text/html":
  mail_text = notification_message.asEntireHTML(
    substitution_method_parameter_dict={'mapping_dict':notification_mapping_dict})
else:
  mail_text = notification_message.asText(
    substitution_method_parameter_dict={'mapping_dict':notification_mapping_dict})

portal.portal_notifications.sendMessage(
  sender=sender,
  recipient=recipient,
  subject=notification_message.getTitle(),
  message=mail_text,
  message_text_format=notification_message.getContentType(),
  notifier_list=(portal.portal_preferences.getPreferredLoginAndPasswordNotifier(),),
  store_as_event= portal.portal_preferences.isPreferredStoreEvents(),
  event_keyword_argument_dict={'follow_up':context.getRelativeUrl()},
  )

return True
