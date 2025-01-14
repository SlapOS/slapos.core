from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

ndays = 10

subject = 'Acknowledgment: instances deleted'
body = """Dear user,

Despite our last reminder, you still have an unpaid invoice on %s.
We will now delete all your instances.

Regards,
The slapos team
""" % context.getPortalObject().portal_preferences.getPreferredSlaposWebSiteUrl()

return context.RegularisationRequest_checkToTriggerNextEscalationStep(
  delay_period_in_days=ndays,
  current_service_relative_url='service_module/slapos_crm_delete_reminder',
  next_service_relative_url='service_module/slapos_crm_delete_acknowledgement',
  title=subject,
  text_content=body,
  comment='Deleting acknowledgment.',
  notification_message="slapos-crm.delete.reminder.escalation",
  substitution_method_parameter_dict={
    'user_name': context.getDestinationDecisionTitle(),
    'days': ndays
  }
)
