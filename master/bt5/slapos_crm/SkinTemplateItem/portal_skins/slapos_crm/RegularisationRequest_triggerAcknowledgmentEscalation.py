from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()
ndays = 15

subject = 'Reminder: invoice payment requested'
body = """Dear user,

We would like to remind you the unpaid invoice.
If no payment is done during the coming days, we will stop all your current instances to free some hardware resources.

Regards,
Administrator
"""

return context.RegularisationRequest_checkToTriggerNextEscalationStep(
  delay_period_in_days=ndays,
  current_service_relative_url=portal.service_module.slapos_crm_acknowledgement.getRelativeUrl(),
  next_service_relative_url=portal.service_module.slapos_crm_delete_reminder.getRelativeUrl(),
  title=subject,
  text_content=body,
  comment='Stopping reminder.',
  notification_message="slapos-crm.acknowledgment.escalation",
  substitution_method_parameter_dict={
    'user_name': context.getDestinationDecisionTitle(),
    'days': ndays
  }
)
