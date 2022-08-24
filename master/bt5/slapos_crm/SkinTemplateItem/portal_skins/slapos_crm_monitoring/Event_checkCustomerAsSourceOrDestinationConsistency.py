support_request = context.getFollowUpValue(portal_type="Support Request")
error_list = []

if support_request:
  customer = support_request.getDestinationDecision()
  if context.getSource() != customer and \
    customer not in context.getDestinationList() :
    error_list.append(
      'Customer should be source or destination of the event')

return error_list
