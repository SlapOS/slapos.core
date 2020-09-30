from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

notification_message = context.getPortalObject().portal_notifications.getDocumentValue(reference="slapos-crm.delete.reminder.escalation")
if notification_message is None:
  subject = 'Acknowledgment: instances deleted'
  body = """Dear user,

Despite our last reminder, you still have an unpaid invoice on %s.
We will now delete all your instances.

Regards,
The slapos team
""" % context.getPortalObject().portal_preferences.getPreferredSlaposWebSiteUrl()
else:
  subject = notification_message.getTitle()
  body = notification_message.convert(format='text')[1]

return context.RegularisationRequest_checkToTriggerNextEscalationStep(
  delay_period_in_days=10,
  current_service_relative_url='service_module/slapos_crm_delete_reminder',
  next_service_relative_url='service_module/slapos_crm_delete_acknowledgement',
  title=subject,
  text_content=body,
  comment='Deleting acknowledgment.',
)
