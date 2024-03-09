person = state_change['object']
portal = person.getPortalObject()
# Get required arguments
kwargs = state_change.kwargs

# Required args
# Raise TypeError if all parameters are not provided
try:
  support_request_title = kwargs['support_request_title']
  resource = kwargs['support_request_resource']
  description = kwargs['support_request_description']
  # Aggregate can be None, so it isn't included on the kwargs
  aggregate = kwargs.get("support_request_aggregate", None)
except KeyError:
  raise TypeError("Person_requestSupportRequest takes exactly 4 arguments")

tag = "%s_%s_SupportRequestInProgress" % (person.getUid(), 
                               support_request_title)
if (portal.portal_activities.countMessageWithTag(tag) > 0):
  # The software instance is already under creation but can not be fetched from catalog
  # As it is not possible to fetch informations, it is better to raise an error
  raise NotImplementedError(tag)

support_request_portal_type = "Support Request"

module = portal.getDefaultModule(portal_type=support_request_portal_type)
support_request = module.newContent(
  portal_type=support_request_portal_type,
  title=support_request_title,
  description=description,
  resource=resource,
  destination_decision_value=person,
  aggregate=aggregate,
  specialise="sale_trade_condition_module/slapos_ticket_trade_condition",
  activate_kw={'tag': tag}
)
context.REQUEST.set("support_request_relative_url", support_request.getRelativeUrl())

support_request.approveRegistration()
