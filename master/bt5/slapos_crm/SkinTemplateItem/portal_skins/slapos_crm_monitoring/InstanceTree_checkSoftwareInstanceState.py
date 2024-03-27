from DateTime import DateTime
from erp5.component.module.DateUtils import addToDate

instance_tree = context
portal = context.getPortalObject()

if portal.ERP5Site_isSupportRequestCreationClosed():
  # Stop ticket creation
  return

date_check_limit = addToDate(DateTime(), to_add={'hour': -1})

if (date_check_limit - instance_tree.getCreationDate()) < 0:
  # Too early to check
  return

software_instance_list = context.portal_catalog(
  portal_type=["Software Instance", "Slave Instance"],
  specialise__uid=instance_tree.getUid(),
  **{"slapos_item.slap_state": ["start_requested"]})

# Check if at least one software Instance is Allocated
notification_message_reference = None
for instance in software_instance_list:
  if (date_check_limit - instance.getCreationDate()) < 0:
    continue

  if instance.getSlapState() != "start_requested":
    continue

  compute_partition = instance.getAggregateValue()
  if compute_partition is None:
    notification_message_reference = 'slapos-crm-instance-tree-instance-allocation.notification'
  elif (instance.getPortalType() == "Software Instance") and \
    (compute_partition.getParentValue().getMonitorScope() == "enabled") and \
    instance.SoftwareInstance_hasReportedError(tolerance=30):

    notification_message_reference = 'slapos-crm-instance-tree-instance-state.notification'

  if notification_message_reference is not None:
    ticket_title = "Instance Tree %s is failing." % context.getTitle()
    error_message = instance.SoftwareInstance_hasReportedError(include_message=True)

    description = "%s contains software instances which are unallocated or reporting errors." % (
            context.getTitle())
    if error_message:
      description += "\n\nMessage: %s" % str(error_message)
    else:
      error_message = "No message!"

    project = context.getFollowUpValue()
    support_request = project.Project_createSupportRequestWithCausality(
      ticket_title,
      description,
      causality=context.getRelativeUrl(),
      destination_decision=context.getDestinationSection()
    )
    if support_request is None:
      return

    event = support_request.SupportRequest_getLastEvent(ticket_title)
    if event is None:
      support_request.Ticket_createProjectEvent(
        ticket_title, 'outgoing', 'Web Message',
        portal.service_module.slapos_crm_information.getRelativeUrl(),
        text_content=description,
        content_type='text/plain',
        notification_message=notification_message_reference,
        #language=XXX,
        substitution_method_parameter_dict={
          'instance_tree_title':context.getTitle(),
          'instance': instance.getTitle(),
          'error_text': error_message
        }
      )
    return
