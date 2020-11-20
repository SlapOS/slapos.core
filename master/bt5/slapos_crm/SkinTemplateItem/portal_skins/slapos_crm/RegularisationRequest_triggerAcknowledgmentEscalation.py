from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()
language = "en"
recipient = context.getDestinationSectionValue()
if recipient is not None:
  language = recipient.getLanguage("en")

notification_message = portal.portal_notifications.getDocumentValue(
  language=language, reference="slapos-crm.acknowledgment.escalation")

if notification_message is None:
  subject = 'Reminder: invoice payment requested'
  body = """Dear user,

We would like to remind you the unpaid invoice you have on %s.
If no payment is done during the coming days, we will stop all your current instances to free some hardware resources.

Regards,
The slapos team
""" % context.getPortalObject().portal_preferences.getPreferredSlaposWebSiteUrl()

else:
  notification_mapping_dict = {
     'user_name': context.getDestinationSectionTitle()}

  subject = notification_message.getTitle()

  # Preserve HTML else convert to text
  if notification_message.getContentType() == "text/html":
    body = notification_message.asEntireHTML(
        substitution_method_parameter_dict={'mapping_dict':notification_mapping_dict})
  else:
    body = notification_message.asText(
        substitution_method_parameter_dict={'mapping_dict':notification_mapping_dict})

return context.RegularisationRequest_checkToTriggerNextEscalationStep(
  delay_period_in_days=15,
  current_service_relative_url='service_module/slapos_crm_acknowledgement',
  next_service_relative_url='service_module/slapos_crm_stop_reminder',
  title=subject,
  text_content=body,
  comment='Stopping reminder.',
)
