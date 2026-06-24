portal = context.getPortalObject()
compute_node = context

if (context.getPortalType() != "Compute Node"):
  return
if compute_node.getValidationState() != 'validated':
  return
if compute_node.getAllocationScope() == 'close/maintenance':
  return

project = compute_node.getFollowUpValue()
if project.Project_isSupportRequestCreationClosed():
  return

allocation_supply_list = portal.portal_catalog(
  portal_type='Allocation Supply',
  validation_state='validated',
  destination_project__uid=compute_node.getFollowUpUid(),
  aggregate__uid=compute_node.getUid(),
  limit=1,
)
if len(allocation_supply_list) != 0:
  return



# Propose to set the node in maintenance
ticket_title = 'Compute Node %s has no allocation supply' % compute_node.getReference()
ticket_description = """The Compute Node "%s" (%s) has no related Allocation Supply.

If you do not plan to configure any, while keeping the node in the project, please set the allocation scope to: closed for maintenance

This will help understanding which node are not supposed to have any service.

Thanks in advance.
""" % (compute_node.getTitle(), compute_node.getReference())

# Create the ticket
support_request = project.Project_createTicketWithCausality(
  'Support Request',
  ticket_title,
  ticket_description,
  causality=compute_node.getRelativeUrl(),
  destination_decision=project.getDestination()
)

if support_request is not None:
  event = support_request.Ticket_createProjectEvent(
    ticket_title, 'outgoing', 'Web Message',
    portal.service_module.slapos_crm_information.getRelativeUrl(),
    ticket_description,
    content_type='text/plain',
    #notification_message=error_dict['notification_message_reference'],
    #language=XXX,
    #substitution_method_parameter_dict=error_dict
  )
  support_request.reindexObject(activate_kw=activate_kw)
  event.reindexObject(activate_kw=activate_kw)
return support_request
