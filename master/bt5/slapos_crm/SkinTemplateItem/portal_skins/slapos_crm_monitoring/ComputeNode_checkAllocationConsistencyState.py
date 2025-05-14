from DateTime import DateTime
import six
portal = context.getPortalObject()

# Remote Node has no monitor scope.
if context.getPortalType() == "Compute Node" and \
         context.getMonitorScope() == "disabled":
  return

project = context.getFollowUpValue()
if project.Project_isSupportRequestCreationClosed():
  return

all_node_error_dict = {}
# Since we would like a single ticket per node,
# we aggregate all detected errors
for compute_partition in context.contentValues(portal_type='Compute Partition'):
  if compute_partition.getSlapState() == 'busy':
    compute_partition_error_dict = compute_partition.ComputePartition_checkAllocationConsistencyState()
    for node_relative_url, node_release_dict in compute_partition_error_dict.items():
      if node_relative_url not in all_node_error_dict:
        all_node_error_dict[node_relative_url] = {}
      for node_release_url, node_type_dict in node_release_dict.items():
        if node_release_url not in all_node_error_dict[node_relative_url]:
          all_node_error_dict[node_relative_url][node_release_url] = {}
        for node_type, failing_instance in node_type_dict.items():
          all_node_error_dict[node_relative_url][node_release_url][node_type] = failing_instance

ticket_list = []
# Generate a single ticket per non consistent node
ticket_portal_type = 'Support Request'
for non_consistent_node_relative_url in all_node_error_dict:
  non_consistent_node = portal.restrictedTraverse(non_consistent_node_relative_url)
  non_consistent_node_title = non_consistent_node.getTitle()
  non_consistent_node_reference = non_consistent_node.getReference()
  # Use same dict from monitoring so we are consistent while writting
  # Notification messages
  compute_node_error_dict = all_node_error_dict[non_consistent_node_relative_url]
  error_dict = {
    'should_notify': True,
    'ticket_title': "%s has missing allocation supplies." % non_consistent_node_title,
    'ticket_description': None,
    'notification_message_reference': 'slapos-crm-compute_node_check_allocation_supply_state.notification',
    'compute_node_title': non_consistent_node_title,
    'compute_node_id': non_consistent_node_reference,
    'last_contact': None,
    'issue_document_reference': None,
    'message': None,
    'compute_node_error_dict': compute_node_error_dict
  }

  message = """The following contains instances that has Software Releases/Types that are missing on this %s's Allocation Supply configuration:

  """ % non_consistent_node.getPortalType()

  for sofware_release_url in compute_node_error_dict:
    message += """
    * Software Release: %s
""" % sofware_release_url
    for sofware_type, instance in six.iteritems(compute_node_error_dict[sofware_release_url]):
      message += """     * Software Type: %s (ie: %s)
""" % (sofware_type, instance.getTitle())

  error_dict['message'] = message
  support_request = project.Project_createTicketWithCausality(
    ticket_portal_type,
    error_dict['ticket_title'],
    error_dict['ticket_description'],
    causality=non_consistent_node.getRelativeUrl(),
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
    ticket_list.append(support_request)

if not ticket_list:
  return
if len(ticket_list) == 1:
  return ticket_list[0]
return ticket_list
