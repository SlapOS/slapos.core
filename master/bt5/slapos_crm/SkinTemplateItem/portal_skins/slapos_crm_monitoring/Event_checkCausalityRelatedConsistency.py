support_request = context.getCausalityRelatedValue(portal_type="Support Request")

error_list = []

if support_request:
  if context.getSource() != support_request.getDestinationDecision():
    error_list.append(
      'Sender should be the customer')
    if fixit:
      context.edit(source=support_request.getDestinationDecision())
      assert context.getSource() == support_request.getDestinationDecision()

  if context.getDestination() != support_request.getSourceSection():
    error_list.append(
      'Destination should be the slapos organisation')
    if fixit:
      context.edit(destination=support_request.getSourceSection())
      assert context.getDestination() == support_request.getSourceSection()

return error_list
