portal = context.getPortalObject()

if context.getSimulationState() != "ordered":
  return

# Instance is ok, we should move foward
portal = context.getPortalObject()
sender = context.getSourceSectionValue(portal_type="Person")
recipient = context.getDestinationSectionValue(portal_type="Person")

# Get message from catalog
notification_reference = 'subscription_request-payment-is-ready'

language = context.getLanguage(recipient.getLanguage())

# This implies the language to notify.
notification_message = portal.portal_notifications.getDocumentValue(
    reference=notification_reference, language=language)

if notification_message is None:
  raise ValueError('Unable to found Notification Message with reference "%s".' % notification_reference)

# Set notification mapping
notification_mapping_dict = {
  'name': recipient.getTitle(),
  'subscription_title': context.getTitle(),
  # Possible more actions goes here
  'payment_relative_relative_url': invoice.getRelativeUrl()}

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
