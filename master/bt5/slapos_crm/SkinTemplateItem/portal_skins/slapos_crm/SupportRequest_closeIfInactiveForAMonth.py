from Products.ERP5Type.Errors import UnsupportedWorkflowMethod
from DateTime import DateTime
portal = context.getPortalObject()

if context.getSimulationState() != "suspended":
  return

if context.getResource() == "service_module/slapos_crm_monitoring":
  return

limit_date = DateTime() - 31

if context.getModificationDate() < limit_date:
  message = """ This ticket has been closed based on the following policy: Support is authorized to close any tickets assigned to a customer for over a month without feedback (customers have the option to reopen the ticket if needed).
  """
  event_title = "Ticket Closed for Inactivity"
  event = context.Ticket_createProjectEvent(
    event_title, 'outgoing', 'Web Message',
    portal.service_module.slapos_crm_information.getRelativeUrl(),
    text_content=message,
    content_type='text/plain',
  )
  event.reindexObject(activate_kw=activate_kw)
  try:
    context.validate()
  except UnsupportedWorkflowMethod:
    pass
  context.invalidate(comment=event_title)
  context.reindexObject(activate_kw=activate_kw)
  return event
