from DateTime import DateTime

compute_node = context
portal = context.getPortalObject()
allocation_scope = compute_node.getAllocationScope()
compute_node_reference = compute_node.getReference()

if allocation_scope not in ['open/public', 'open/friend', 'open/personal']:
  return

if allocation_scope == target_allocation_scope:
  # already changed
  return

person = compute_node.getSourceAdministrationValue(portal_type="Person")
if not person:
  return

if check_service_provider and person.Person_isServiceProvider():
  return

edit_kw = {
  'allocation_scope': target_allocation_scope,
}

# Create a ticket (or re-open it) for this issue!
request_title = 'Allocation scope of %s changed to %s' % (compute_node_reference,
                                               target_allocation_scope)
request_description = 'Allocation scope has been changed to ' \
                     '%s for %s' % (target_allocation_scope, compute_node_reference)

support_request = context.Base_generateSupportRequestForSlapOS(
               request_title,
               request_description,
               compute_node.getRelativeUrl()
             )

if support_request is not None:
  if support_request.getSimulationState() != "validated":
    support_request.validate()

  # Send notification message
  message = request_description
  notification_message = portal.portal_notifications.getDocumentValue(
                 reference=notification_message_reference)

  if notification_message is not None:
    mapping_dict = {'compute_node_title':compute_node.getTitle(),
                    'compute_node_id':compute_node_reference,
                    'compute_node_url':compute_node.getRelativeUrl(),
                    'allocation_scope':allocation_scope}
  
    message = notification_message.asText(
              substitution_method_parameter_dict={'mapping_dict': mapping_dict})

  event = support_request.SupportRequest_trySendNotificationMessage(
           request_title, message, person.getRelativeUrl())

  if event is not None:
    # event added, suspend ticket
    if portal.portal_workflow.isTransitionPossible(support_request, 'suspend'):
      support_request.suspend()
  elif not force:
    return support_request

  compute_node.edit(**edit_kw)
  return support_request

elif force:
  # Update compute_node event if ticket is not created
  compute_node.edit(**edit_kw)
