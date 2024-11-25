from DateTime import DateTime
portal = context.getPortalObject()

if context.getMonitorScope() == "disabled":
  return

project = context.getFollowUpValue()
if project.Project_isSupportRequestCreationClosed():
  return

# Check if there is another consistency ticket already issued
# ....

compute_node_error_dict = {}
reference = context.getReference()
compute_node_title = context.getTitle()

# Use same dict from monitoring so we are consistent while writting
# Notification messages
error_dict = {
        'should_notify': None,
        'ticket_title': "%s has inconsistent allocated instances" % compute_node_title,
        'ticket_description': None,
        'notification_message_reference': None,
        'compute_node_title': compute_node_title,
        'compute_node_id': reference,
        'last_contact': None,
        'issue_document_reference': None,
        'message': None,
        'compute_node_error_dict': {}
      }

# Since we would like a single ticket per compute node do all at once:
for compute_partition in context.contentValues(portal_type='Compute Partition'):
  if compute_partition.getSlapState() == 'busy':
    sla_error = compute_partition.ComputePartition_checkAllocatedSlaState()
    allocation_supply_error = compute_partition.ComputePartition_checkAllocatedSupplyState()
    compute_node_error_dict[compute_partition.getRelativeUrl()] = {
      'sla_error': sla_error,
      'allocation_supply_error': allocation_supply_error
    }
    if sla_error is not None or allocation_supply_error is not None:
      error_dict['should_notify'] = True

if not error_dict['should_notify']:
  return

## Write minimal message here, and replace the dict
error_dict['message'] = compute_node_error_dict

support_request = project.Project_createTicketWithCausality(
  'Support Request',
  error_dict['ticket_title'],
  error_dict['ticket_description'],
  causality=context.getRelativeUrl(),
  destination_decision=project.getDestination()
)

if support_request is not None:
  support_request.Ticket_createProjectEvent(
    error_dict['ticket_title'], 'outgoing', 'Web Message',
    portal.service_module.slapos_crm_information.getRelativeUrl(),
    text_content=error_dict['message'],
    content_type='text/plain',
    notification_message=error_dict['notification_message_reference'],
    #language=XXX,
    substitution_method_parameter_dict=error_dict
  )
return support_request
