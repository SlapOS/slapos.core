from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()
ndays = 10

subject = 'Acknowledgment: instances deleted'
body = """Dear user,

Despite our last reminder, you still have an unpaid invoices.
We will now delete all your instances.

Regards,
Administrator
"""

return context.RegularisationRequest_checkToTriggerNextEscalationStep(
  delay_period_in_days=ndays,
  current_service_relative_url=portal.service_module.slapos_crm_delete_reminder.getRelativeUrl(),
  next_service_relative_url=portal.service_module.slapos_crm_delete_reminder.getRelativeUrl(),
  title=subject,
  text_content=body,
  comment='Deleting acknowledgment.',
  notification_message="slapos-crm.delete.reminder.escalation",
  substitution_method_parameter_dict={
    'user_name': context.getDestinationDecisionTitle(),
    'days': ndays
  }
)
