from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()
person = context.getDestinationDecisionValue(portal_type='Person')
if (person is None):
  return

##################################################################
# Search conflicting customer workgroup assignment:
# (person can NOT have 2 customer workgroup assignment, or person.requestInstance will not work)
workgroup_assignment_request_list = portal.portal_catalog(
  portal_type='Assignment Request',
  simulation_state='validated',
  destination__portal_type='Workgroup',
  destination_decision__uid=person.getUid(),
)
if len(workgroup_assignment_request_list) <= 1:
  return
workgroup_uid_list = [x.getDestinationUid() for x in workgroup_assignment_request_list]

conflicting_assignment_request_list = [x.getObject() for x in portal.portal_catalog(
  portal_type='Assignment Request',
  simulation_state='validated',
  destination_decision__uid=workgroup_uid_list,
  function__uid=portal.portal_categories.function.customer.getUid(),
  group_by=['destination_project_uid'],
  select_list=['COUNT(*)']
) if (1 < x['COUNT(*)'])]

if conflicting_assignment_request_list:
  # Propose to close one assignment
  conflicting_assignment_request = conflicting_assignment_request_list[0]
  conflicting_project = conflicting_assignment_request.getDestinationProjectValue()

  ticket_title = 'Conflicting customer Workgroup assignments for: %s' % person.getTitle()
  ticket_description = """The user "%s" has conflicting workgroup assignments for project %s.

  This configuration prevents user to create new Instance Tree inside the project.

  There are 2 possibility:
    - remove user profile from one workgroup assignment
    - remove project's customer assignment from a workgroup

  Thanks in advance.
  """ % (person.getTitle(), conflicting_project.getReference())

  # Create the ticket
  support_request = person.Person_createTicketWithCausality(
    'Support Request',
    ticket_title,
    ticket_description,
    causality=conflicting_project.getRelativeUrl(),
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
