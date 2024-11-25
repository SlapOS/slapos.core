from DateTime import DateTime
portal = context.getPortalObject()

# Remote Node has no monitor scope.
if context.getPortalType() == "Compute Node" and \
         context.getMonitorScope() == "disabled":
  return

project = context.getFollowUpValue()
if project.Project_isSupportRequestCreationClosed():
  return

# Exceptionally, we pre-check if the computer has a ticket already
# Since calculation is a bit expensive to "just try".
monitor_service_uid = portal.service_module.slapos_crm_monitoring.getUid()
ticket_portal_type = "Support Request"
if portal.portal_catalog.getResultValue(
  portal_type=ticket_portal_type,
  resource__uid=monitor_service_uid,
  simulation_state=["validated", "submitted", "suspended"],
  causality__uid=context.getUid(),
) is not None:
  return

reference = context.getReference()
compute_node_title = context.getTitle()

# Use same dict from monitoring so we are consistent while writting
# Notification messages
error_dict = {
        'should_notify': None,
        'ticket_title': "%s has inconsistent allocated instances" % compute_node_title,
        'ticket_description': None,
        'notification_message_reference': 'slapos-crm-compute_node_check_allocation_supply_state.notification',
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
    compute_partition_error_dict = compute_partition.ComputePartition_checkAllocationConsistencyState()
    if compute_partition_error_dict:
      error_dict['compute_node_error_dict'][compute_partition.getId()] = compute_partition_error_dict
      error_dict['should_notify'] = True

if not error_dict['should_notify']:
  return


error_msg = ""
for _compute_node_error_dict in error_dict['compute_node_error_dict'].values():
  for instance_error_dict in _compute_node_error_dict.values():
    # Add Allocation Supply Error
    allocation_supply_error = instance_error_dict.get('allocation_supply_error', None)
    if allocation_supply_error:
      error_msg += """  * %s
""" % allocation_supply_error

    # Append sla errors
    sla_error_list = instance_error_dict.get('sla_error_list', None)
    if sla_error_list:
      for entry in sla_error_list:
        error_msg += """  * %s
""" % entry

error_dict['message'] = """%s:

%s
""" % (error_dict['ticket_title'], error_msg)

support_request = project.Project_createTicketWithCausality(
  ticket_portal_type,
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
