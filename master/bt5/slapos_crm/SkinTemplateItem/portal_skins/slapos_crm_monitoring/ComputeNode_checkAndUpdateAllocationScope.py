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

support_request = person.Base_getSupportRequestInProgress(
  title=request_title,
  aggregate=context.getRelativeUrl()
)

if support_request is None:
  person.notify(support_request_title=request_title,
              support_request_description=request_description,
              aggregate=context.getRelativeUrl())

  support_request_relative_url = context.REQUEST.get("support_request_relative_url")
  support_request = portal.restrictedTraverse(support_request_relative_url)

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

  event = support_request.SupportRequest_getLastEvent(request_title)
  if event is None:
    support_request.notify(message_title=request_title, message=message)
    event = support_request.REQUEST.get("ticket_notified_item")

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
