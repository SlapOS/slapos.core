event = context.Ticket_getCausalityValue()
error_list = []

if event:
  if event.getSource() != context.getDestinationDecision():
    error_list.append(
      'Sender of the related event should be the customer')

  if event.getDestination() != context.getSourceSection():
    error_list.append(
      'Destination  of the related event should be the slapos organisation')

return error_list
