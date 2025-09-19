from DateTime import DateTime
from Products.ZSQLCatalog.SQLCatalog import SimpleQuery
from erp5.component.module.DateUtils import addToDate
portal = context.getPortalObject()
project = context

if project.Project_isSupportRequestCreationClosed():
  return
if activate_kw is None:
  activate_kw = {}

####################################
# Check if the project is empty
####################################
content_list = portal.portal_catalog(
  portal_type=['Compute Node', 'Instance Tree'],
  validation_state='validated',
  follow_up__uid=project.getUid(),
  limit=1
)
if len(content_list) == 0:
  ticket_title = 'project %s seems outdated' % project.getReference()
  ticket_description = """This empty Project seems not used anymore.

If not used anymore, please contact your sale manager to close it.

Thanks in advance.
  """

  support_request = project.Project_createTicketWithCausality(
    'Support Request',
    ticket_title,
    ticket_description,
    causality=project.getRelativeUrl(),
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


####################################
# Check outdated compute node
####################################
# Search the non allocable Compute Node, without any instances
# and not contacting the slapos master anymore
# Those are candidates to be close/forever
portal.portal_catalog.searchAndActivate(
  portal_type='Compute Node',
  # check old enough nodes, to give user some time to configure it
  creation_date=SimpleQuery(
    creation_date=addToDate(DateTime(), to_add={'day': -90}),
    comparison_operator="<"
  ),
  validation_state='validated',
  capacity_scope__id='close',

  follow_up__uid=project.getUid(),
  method_id='ComputeNode_checkForGarbageCollect',
  method_kw={'activate_kw': activate_kw},
  activate_kw=activate_kw
)


####################################
# Check software instances to garbage collect
####################################
portal.portal_catalog.searchAndActivate(
  portal_type=['Software Instance'],
  # check instance not touched for some times, to give slapgrid some time to handle it
  modification_date=SimpleQuery(
    modification_date=addToDate(DateTime(), to_add={'day': -1}),
    comparison_operator="<",
  ),
  # Search correctly destroyed instances (and not instance tree)...
  validation_state='invalidated',
  # ...with not destroyed sub instances...
  successor__validation_state="validated",
  # ... and with a validated instance tree
  specialise__validation_state='validated',

  method_id='SoftwareInstance_checkForGarbageCollect',
  method_kw={'activate_kw': activate_kw},
  activate_kw=activate_kw
)
