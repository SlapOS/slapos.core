""" Close Support Request which are related to a Destroy Requested Instance. """
portal = context.getPortalObject()

pending_ticket_list_amount = len(context.Person_getSlapOSPendingTicket())

# Send Notification message
message = """ You have %s pending tickets  """ % pending_ticket_list_amount

notification_message = portal.portal_notifications.getDocumentValue(
    reference="slapos-crm-person-pending-ticket-notification")

if notification_message is not None:
  mapping_dict = {'username': context.getTitle(),
                  'amount': pending_ticket_list_amount}

  message = notification_message.asText(
              substitution_method_parameter_dict={'mapping_dict':mapping_dict})

return message
