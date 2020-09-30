from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

notification_message = context.getPortalObject().portal_notifications.getDocumentValue(reference="slapos-crm.stop.reminder.escalation")
if notification_message is None:
  subject = 'Acknowledgment: instances stopped'
  body = """Dear user,

Despite our last reminder, you still have an unpaid invoice on %s.
We will now stop all your current instances to free some hardware resources.

Regards,
The slapos team
""" % context.getPortalObject().portal_preferences.getPreferredSlaposWebSiteUrl()
else:
  subject = notification_message.getTitle()
  body = notification_message.convert(format='text')[1]

return context.RegularisationRequest_checkToTriggerNextEscalationStep(
  delay_period_in_days=7,
  current_service_relative_url='service_module/slapos_crm_stop_reminder',
  next_service_relative_url='service_module/slapos_crm_stop_acknowledgement',
  title=subject,
  text_content=body,
  comment='Stopping acknowledgment.',
)
