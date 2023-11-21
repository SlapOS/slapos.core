from zExceptions import Unauthorized

if REQUEST is not None:
  raise Unauthorized

event = context
portal = context.getPortalObject()
support_request = portal.restrictedTraverse(follow_up_relative_url)

project_value = support_request.getSourceProjectValue()
destination_decision = support_request.getDestinationDecision()

source_project_value = None
destination_project_value = None

if event.getSource() == destination_decision:
  destination_project_value = project_value
if event.getDestination() == destination_decision:
  source_project_value = project_value

if (source_project_value is None) and (destination_project_value is None):
  # Consider it was an outgoing event
  source_project_value = project_value

edit_kw = {
  'follow_up_value': support_request,
  'resource_value': event.getResourceValue(),
  'use_value': event.getUseValue(),
  'quantity_unit_value': event.getQuantityUnitValue(),
  'price_currency_value': event.getPriceCurrencyValue(),
  'causality_value': event.getCausalityValue(portal_type=portal.getPortalEventTypeList()),
  'source_value': event.getSourceValue(),
  'destination_value': event.getDestinationValue(),
  'source_project_value': source_project_value,
  'destination_project_value': destination_project_value
}

event.setCategoryList([])
event.edit(**edit_kw)
