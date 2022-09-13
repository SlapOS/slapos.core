amount = len(context.Person_getSlapOSPendingTicket())
if amount > 0:
  title, reminder_message = context.Person_getSlapOSPendingTicketMessageTemplate()
  return context.Person_sendSlapOSPendingTicketNotification(
    title,
    reminder_message,
    batch_mode=1
  )
