from erp5.component.module.DateUtils import addToDate

portal = context.getPortalObject()
instance_tree = context
project = instance_tree.getFollowUpValue()

if (instance_tree.getPortalType() != "Instance Tree"):
  return
if instance_tree.getValidationState() != 'validated':
  # Instance tree was invalidated, nothing to do
  return
if addToDate(DateTime(), to_add={'day': -1}) < instance_tree.getCreationDate():
  # check instance tree not touched for some times,
  # to give manager time to configure the project
  return

# Search for an Subscription Request
# to check if the project configuration allow such software release
if portal.portal_catalog.getResultValue(
  portal_type='Subscription Request',
  aggregate__uid=instance_tree.getUid()
) is not None:
  # No need to create a new ticket in such case
  return



ticket_title = 'Instance tree %s is not allowed' % instance_tree.getReference()
ticket_description = """This instance tree's Software Release / Type is not allowed in this project.

Please configure the project to accept it, or destroy this instance tree.
"""

support_request = project.Project_createTicketWithCausality(
  'Support Request',
  ticket_title,
  ticket_description,
  causality=instance_tree.getRelativeUrl(),
  destination_decision=instance_tree.getDestinationSection()
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
