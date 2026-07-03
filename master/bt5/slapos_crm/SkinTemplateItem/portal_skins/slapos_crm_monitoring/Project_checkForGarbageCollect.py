from DateTime import DateTime
from Products.ZSQLCatalog.SQLCatalog import SimpleQuery, NegatedQuery
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
  portal_type=['Compute Node', 'Instance Tree', 'Instance Node'],
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
  strict__allocation_scope__uid=NegatedQuery(SimpleQuery(strict__allocation_scope__uid=portal.portal_categories.allocation_scope.close.maintenance.getUid())),

  follow_up__uid=project.getUid(),
  method_id='ComputeNode_checkForGarbageCollect',
  method_kw={'activate_kw': activate_kw},
  activate_kw=activate_kw
)


####################################
# Check outdated instance node
####################################
# Search Instance Node related to destroyed Software Instance
portal.portal_catalog.searchAndActivate(
  portal_type='Instance Node',
  validation_state='validated',
  specialise__validation_state='invalidated',
  follow_up__uid=project.getUid(),

  method_id='InstanceNode_checkForGarbageCollect',
  method_kw={'activate_kw': activate_kw},
  activate_kw=activate_kw
)


####################################
# Check software instances to garbage collect
####################################
portal.portal_catalog.searchAndActivate(
  portal_type=['Software Instance'],
  follow_up__uid=project.getUid(),
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


####################################
# Check instance tree to garbage collect
# Instance tree without any Software Instance
####################################
select_dict= {'successor__uid': None}
portal.portal_catalog.searchAndActivate(
  portal_type='Instance Tree',
  follow_up__uid=project.getUid(),
  validation_state='validated',
  left_join_list=select_dict.keys(),

  # check instance tree not touched for some times,
  # to give manager time to configure the project
  creation_date=SimpleQuery(
    creation_date=addToDate(DateTime(), to_add={'day': -1}),
    comparison_operator="<",
  ),

  method_id='InstanceTree_checkForGarbageCollect',
  method_kw={'activate_kw': activate_kw},
  activate_kw=activate_kw,

  **select_dict
)

####################################
# Check allocation supply to garbage collect
# Allocation Supply without any Node
####################################
select_dict= {'aggregate__uid': None}
portal.portal_catalog.searchAndActivate(
  portal_type='Allocation Supply',
  validation_state=['draft', 'invalidated', 'validated'],
  destination_project__uid=project.getUid(),
  left_join_list=select_dict.keys(),

  method_id='AllocationSupply_checkForGarbageCollect',
  method_kw={'activate_kw': activate_kw},
  activate_kw=activate_kw,

  **select_dict
)

####################################
# Check not configured compute node
####################################
# Search Compute Node, without any allocation supply
# Those are candidates to be close/maintenance
configured_node_uid_list = [-1]
for sql_result in portal.portal_catalog(
  portal_type='Allocation Supply',
  validation_state='validated',
  destination_project__uid=project.getUid(),
):
  configured_node_uid_list.extend(sql_result.getAggregateUidList())
portal.portal_catalog.searchAndActivate(
  portal_type='Compute Node',
  follow_up__uid=project.getUid(),
  # check old enough nodes, to give user some time to configure it
  creation_date=SimpleQuery(
    creation_date=addToDate(DateTime(), to_add={'day': -90}),
    comparison_operator="<"
  ),
  validation_state='validated',
  strict__allocation_scope__uid=NegatedQuery(SimpleQuery(strict__allocation_scope__uid=[
    portal.portal_categories.allocation_scope.close.maintenance.getUid(),
    portal.portal_categories.allocation_scope.close.forever.getUid(),
  ])),
  uid=NegatedQuery(SimpleQuery(uid=configured_node_uid_list)),
  method_id='ComputeNode_checkForMaintenance',
  method_kw={'activate_kw': activate_kw},
  activate_kw=activate_kw
)
