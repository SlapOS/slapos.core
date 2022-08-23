support_request = context.getFollowUpValue(portal_type="Support Request")
error_list = []

if support_request:
  customer = support_request.getDestinationDecision()
  if context.getSource() != customer and \
    customer not in context.getDestinationList() :
    error_list.append(
      'Customer should be source or destination of the event')
    if fixit:
      destination_list = context.getDestinationList()
      destination_list.append(customer)
      context.edit(destination=customer)
      assert customer in context.getDestinationList()

return error_list
