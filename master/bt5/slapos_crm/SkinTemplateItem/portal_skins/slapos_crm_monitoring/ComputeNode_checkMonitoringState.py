from DateTime import DateTime
portal = context.getPortalObject()

if context.getMonitorScope() == "disabled":
  return
  
project = context.getFollowUpValue()
if project.Project_isSupportRequestCreationClosed():
  return

error_dict = context.ComputeNode_getReportedErrorDict()
if not error_dict['should_notify']:
  return

support_request = project.Project_createSupportRequestWithCausality(
  error_dict['ticket_title'],
  error_dict['ticket_description'],
  causality=context.getRelativeUrl(),
  destination_decision=project.getDestination()
)

if support_request is not None:
  support_request.Ticket_createProjectEvent(
    error_dict['ticket_title'], 'outgoing', 'Web Message',
    portal.service_module.slapos_crm_information.getRelativeUrl(),
    text_content=error_dict['ticket_description'],
    content_type='text/plain',
    notification_message=error_dict['notification_message_reference'],
    #language=XXX,
    substitution_method_parameter_dict=error_dict
  )
return support_request
