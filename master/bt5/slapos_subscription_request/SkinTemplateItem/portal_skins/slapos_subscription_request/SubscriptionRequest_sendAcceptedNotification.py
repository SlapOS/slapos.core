portal = context.getPortalObject()
sender = context.getSourceSectionValue(portal_type="Person")
recipient = context.getDestinationSectionValue(portal_type="Person")

#Define the type of notification
notification_type = "without-password"
if password:
  notification_type = "with-password"

language = context.getLanguage(recipient.getLanguage())

#Get message from catalog
notification_reference = 'subscription_request-confirmation-%s' % notification_type
notification_message = portal.portal_notifications.getDocumentValue(reference=notification_reference,
                                                                    language=language)
if notification_message is None:
  raise ValueError('Unable to found Notification Message with reference "%s".' % notification_reference)

if reference is None:
  login_list = recipient.searchFolder(portal_type="ERP5 Login")
  if login_list:
    reference = login_list[0].getReference()

#Set notification mapping
notification_mapping_dict = {
  'login_name': reference,
  'name': recipient.getTitle()}

if password:
  notification_mapping_dict.update(
                            {'login_password' : password})

#Preserve HTML else convert to text
if notification_message.getContentType() == "text/html":
  mail_text = notification_message.asEntireHTML(
    substitution_method_parameter_dict={'mapping_dict':notification_mapping_dict})
else:
  mail_text = notification_message.asText(
    substitution_method_parameter_dict={'mapping_dict':notification_mapping_dict})

# Send email
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
