from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

ndays = 7
subject = 'Last reminder: invoice payment requested'
body = """Dear user,

We would like to remind you the unpaid invoice you have on %s.
If no payment is done during the coming days, we will delete all your instances.

Regards,
The slapos team
""" % context.getPortalObject().portal_preferences.getPreferredSlaposWebSiteUrl()

return context.RegularisationRequest_checkToTriggerNextEscalationStep(
  delay_period_in_days=ndays,
  current_service_relative_url='service_module/slapos_crm_stop_acknowledgement',
  next_service_relative_url='service_module/slapos_crm_delete_reminder',
  title=subject,
  text_content=body,
  comment='Deleting reminder.',
  notification_message="slapos-crm.stop.acknowledgment.escalation",
  substitution_method_parameter_dict={
    'user_name': context.getDestinationSectionTitle(),
    'days': ndays
  }
)
