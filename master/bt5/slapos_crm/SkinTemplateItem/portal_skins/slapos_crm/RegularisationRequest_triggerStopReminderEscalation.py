from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()
ndays = 7

subject = 'Acknowledgment: instances stopped'
body = """Dear user,

Despite our last reminder, you still have an unpaid invoice.
We will now stop all your current instances to free some hardware resources.

Regards,
Administrator
"""

return context.RegularisationRequest_checkToTriggerNextEscalationStep(
  delay_period_in_days=ndays,
  current_service_relative_url=portal.service_module.slapos_crm_stop_reminder.getRelativeUrl(),
  next_service_relative_url=portal.service_module.slapos_crm_stop_acknowledgement.getRelativeUrl(),
  title=subject,
  text_content=body,
  comment='Stopping acknowledgment.',
  notification_message="slapos-crm.stop.reminder.escalation",
  substitution_method_parameter_dict={
    'user_name': context.getDestinationDecisionTitle(),
    'days': ndays
  }
)
