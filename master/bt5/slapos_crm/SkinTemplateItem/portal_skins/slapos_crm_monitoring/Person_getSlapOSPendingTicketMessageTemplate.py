portal = context.getPortalObject()
pending_ticket_list_amount = len(context.Person_getSlapOSPendingTicket())

notification_message = portal.portal_notifications.getDocumentValue(
    reference="slapos-crm-person-pending-ticket-notification")

if notification_message is not None:
  mapping_dict = {'username': context.getTitle(),
                  'amount': pending_ticket_list_amount,
                  'website': portal.portal_preferences.getPreferredSlaposWebSiteUrl()}

  return notification_message.getTitle(), notification_message.asText(
              substitution_method_parameter_dict={'mapping_dict': mapping_dict})

message = """ You have %s pending tickets  """ % pending_ticket_list_amount,

return message, message
