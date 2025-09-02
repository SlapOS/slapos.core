from DateTime import DateTime
from Products.ZSQLCatalog.SQLCatalog import SimpleQuery
from erp5.component.module.DateUtils import addToDate

portal = context.getPortalObject()
compute_node = context

if (context.getPortalType() != "Compute Node"):
  return
if compute_node.getCapacityScope() != 'close':
  return
if compute_node.getValidationState() != 'validated':
  return

project = compute_node.getFollowUpValue()
if project.Project_isSupportRequestCreationClosed():
  return

last_access_info = compute_node.getLastAccessDate()
if last_access_info != "Compute Node didn't contact the server":
  return

# Check if the server still has some instances
has_busy_partition = False
for partition in compute_node.contentValues(portal_type='Compute Partition'):
  if partition.getSlapState() == 'busy':
    has_busy_partition = True
    break

if has_busy_partition:
  # Search all software instances which were never reported as correctly destroyed
  # If their node only contains instance to destroy, and does not contact the slapos master,
  # it is nearly sure it will never contact it anymore
  # Propose to close/forever and force destruction manually

  not_destroyed_busy_partition_list = []

  for sql_result in portal.portal_catalog(
    portal_type=['Software Instance'],
    # check instance not touched for some times, to give slapformat some time to handle it
    modification_date=SimpleQuery(
      modification_date=addToDate(DateTime(), to_add={'day': -1}),
      comparison_operator="<"
    ),
    aggregate__parent_uid=compute_node.getUid(),
    validation_state='validated',
    # slap_state='destroy_requested'
  ):
    instance = sql_result.getObject()
    partition = instance.getAggregateValue()
    if partition is None:
      # This is not expected.
      # Do not crash
      continue
    assert partition.getParentValue().getRelativeUrl() == compute_node.getRelativeUrl()
    if instance.getSlapState() == 'destroy_requested':
      not_destroyed_busy_partition_list.append(partition.getId())

  # Check if the server still has some running instances
  # If so, do nothing, as manager may have stop slapos crontabs
  for partition in compute_node.contentValues(portal_type='Compute Partition'):
    if (partition.getSlapState() == 'busy') and (partition.getId() not in not_destroyed_busy_partition_list):
      return

  # Propose to close and invalidate this server
  ticket_title = 'compute_node %s seems outdated' % compute_node.getReference()
  ticket_description = """This Compute Node is not contacting the SlapOS master.

It only contains instances to destroy.

If you could, please run slapos node format to trigger the deletion of all user data.

Then, please change its allocation scope to 'close/forever' to definitely drop its access to the system.

Thanks in advance.
"""


#########################################
# has_busy_partition is False
else:
  ticket_title = 'compute_node %s seems outdated' % compute_node.getReference()
  ticket_description = """This empty Compute Node is not contacting the SlapOS master.

If not used anymore, could you please change its allocation scope to 'close/forever' to definitely drop its access to the system?

Thanks in advance.
"""


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
