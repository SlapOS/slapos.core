""" Close Support Request which are related to a Destroy Requested Instance. """
from Products.ERP5Type.Errors import UnsupportedWorkflowMethod
from DateTime import DateTime
portal = context.getPortalObject()

if context.getSimulationState() != "suspended":
  return

if context.getResource() == "service_module/slapos_crm_monitoring":
  return

limit_date = DateTime() - 31

last_event = context.Ticket_getFollowUpRelatedEventList(sort_on=(("delivery.start_date", "DESC"),), limit=1)
if not last_event:
  return
last_event = last_event[0].getObject()
if last_event.getStartDate() < limit_date:
  message = """ This ticket has been closed based on the following policy: Support is authorized to close any tickets assigned to a customer for over a month without feedback (customers have the option to reopen the ticket if needed).
  """
  ticket_title = "Ticket Closed for Inactivity"
  event = context.Ticket_createProjectEvent(
    ticket_title, 'outgoing', 'Web Message',
    portal.service_module.slapos_crm_information.getRelativeUrl(),
    text_content=message,
    content_type='text/plain',
    notification_message="slapos-crm-support-request-close-destroyed-notification",
    substitution_method_parameter_dict={
      'support_request_title': context.getTitle()
    }
  )

  try:
    context.validate()
  except UnsupportedWorkflowMethod:
    pass
  context.invalidate()
  return event
