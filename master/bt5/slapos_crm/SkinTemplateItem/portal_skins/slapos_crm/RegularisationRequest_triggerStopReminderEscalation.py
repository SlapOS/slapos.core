from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

ndays = 7

subject = 'Acknowledgment: instances stopped'
body = """Dear user,

Despite our last reminder, you still have an unpaid invoice on %s.
We will now stop all your current instances to free some hardware resources.

Regards,
The slapos team
""" % context.getPortalObject().portal_preferences.getPreferredSlaposWebSiteUrl()

return context.RegularisationRequest_checkToTriggerNextEscalationStep(
  delay_period_in_days=ndays,
  current_service_relative_url='service_module/slapos_crm_stop_reminder',
  next_service_relative_url='service_module/slapos_crm_stop_acknowledgement',
  title=subject,
  text_content=body,
  comment='Stopping acknowledgment.',
  notification_message="slapos-crm.stop.reminder.escalation",
  substitution_method_parameter_dict={
    'user_name': context.getDestinationSectionTitle(),
    'days': ndays
  }
)
