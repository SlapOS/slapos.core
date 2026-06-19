portal = context.getPortalObject()
allocation_supply = context
project = allocation_supply.getDestinationProjectValue()

if allocation_supply.getPortalType() != "Allocation Supply":
  return
if allocation_supply.getValidationState() == ['deleted']:
  # If already deleted, nothing to do
  return
if allocation_supply.getAggregate(None) is not None:
  return




ticket_title = 'Allocation Supply %s is not linked to any node' % allocation_supply.getTitle()
ticket_description = """This allocation supply has no linked Node.

Please configure some node on it, or delete this allocation supply.
"""

support_request = project.Project_createTicketWithCausality(
  'Support Request',
  ticket_title,
  ticket_description,
  causality=allocation_supply.getRelativeUrl(),
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
