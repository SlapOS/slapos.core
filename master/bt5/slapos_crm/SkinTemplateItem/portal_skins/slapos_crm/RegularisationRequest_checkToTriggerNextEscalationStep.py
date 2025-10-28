from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()
ticket = context
current_service = portal.restrictedTraverse(current_service_relative_url)
assert current_service.getPortalType() == "Service"

if (ticket.getSimulationState() == 'suspended') and (ticket.getResource() == current_service_relative_url):
  event = portal.portal_catalog.getResultValue(
    portal_type="Web Message",
    resource__uid=current_service.getUid(),
    follow_up__uid=ticket.getUid(),
    simulation_state="delivered",
  )
  if (event is not None) and (DateTime() - event.getStartDate()) > delay_period_in_days:
    ticket.RegularisationRequest_checkToSendUniqEvent(next_service_relative_url, title, text_content, comment,
                                                      notification_message=notification_message,
                                                      substitution_method_parameter_dict=substitution_method_parameter_dict)
    return event.getRelativeUrl()

return None
