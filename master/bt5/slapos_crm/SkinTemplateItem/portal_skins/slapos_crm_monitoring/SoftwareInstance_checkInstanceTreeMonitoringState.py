from DateTime import DateTime
from erp5.component.module.DateUtils import addToDate
portal = context.getPortalObject()

assert context.getPortalType() in ['Software Instance', 'Slave Instance']

instance_tree = context.getSpecialiseValue(portal_type="Instance Tree")
assert instance_tree is not None

project = instance_tree.getFollowUpValue()
if project.Project_isSupportRequestCreationClosed():
  return

date_check_limit = addToDate(DateTime(), to_add={'hour': -1})
if (date_check_limit - instance_tree.getCreationDate()) < 0:
  # Too early to check
  return

software_instance_list = portal.portal_catalog(
  portal_type=["Software Instance", "Slave Instance"],
  specialise__uid=instance_tree.getUid(),
  **{"slapos_item.slap_state": ["start_requested"]})

# Check if at least one software Instance is Allocated
for instance in software_instance_list:
  if (date_check_limit - instance.getCreationDate()) < 0:
    continue

  error_dict = instance.SoftwareInstance_getReportedErrorDict(tolerance=30)
  if error_dict['should_notify']:
    support_request = project.Project_createTicketWithCausality(
      'Support Request',
      error_dict['ticket_title'],
      error_dict['ticket_description'],
      causality=instance_tree.getRelativeUrl(),
      destination_decision=instance_tree.getDestinationSection()
    )
    if support_request is not None:
      support_request.Ticket_createProjectEvent(
        error_dict['ticket_title'], 'outgoing', 'Web Message',
        portal.service_module.slapos_crm_information.getRelativeUrl(),
        text_content=error_dict['ticket_description'],
        content_type='text/plain',
        notification_message=error_dict['notification_message_reference'],
        #language=XXX,
        substitution_method_parameter_dict=error_dict
      )
    return support_request
