""" Close Support Request which are related to a Destroy Requested Instance. """

if context.getSimulationState() == "invalidated":
  return

document = context.getAggregateValue()
if document is not None and document.getSlapState() == "destroy_requested":
  
  person = context.getDestinationDecision(portal_type="Person")
  if not person:
    return 

  if context.getSimulationState() != "invalidated":
    context.invalidate()

  # Send Notification message
  message = """ Closing this ticket as the Instance Tree was destroyed by the user. 
  """

  notification_reference = "slapos-crm-support-request-close-destroyed-notification"
  portal = context.getPortalObject()
  notification_message = portal.portal_notifications.getDocumentValue(
                 reference=notification_reference)

  if notification_message is not None:
    mapping_dict = {'instance_tree_title':document.getTitle()}

    message = notification_message.asText(
              substitution_method_parameter_dict={'mapping_dict':mapping_dict})

  context.notify(message_title="Instance Tree was destroyed was destroyed by the user",
              message=message,
              destination_relative_url=person.getRelativeUrl())

  return context.REQUEST.get("ticket_notified_item")
