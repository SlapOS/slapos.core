""" Close Support Request which are related to a Destroy Requested Instance. """
from Products.ERP5Type.Errors import UnsupportedWorkflowMethod
portal = context.getPortalObject()

if context.getSimulationState() == "invalidated":
  return

document = context.getCausalityValue(portal_type="Instance Tree")
if document is None:
  return

if document.getSlapState() == "destroy_requested":

  # Send Notification message
  message = """ Closing this ticket as the Instance Tree was destroyed by the user.
  """

  ticket_title = "Instance Tree was destroyed was destroyed by the user"
  event = context.Ticket_createProjectEvent(
    ticket_title, 'outgoing', 'Web Message',
    portal.service_module.slapos_crm_information.getRelativeUrl(),
    text_content=message,
    content_type='text/plain',
    notification_message="slapos-crm-support-request-close-destroyed-notification",
    #language=XXX,
    substitution_method_parameter_dict={
      'instance_tree_title': document.getTitle()
    }
  )

  try:
    context.validate()
  except UnsupportedWorkflowMethod:
    pass
  context.invalidate()
  return event
