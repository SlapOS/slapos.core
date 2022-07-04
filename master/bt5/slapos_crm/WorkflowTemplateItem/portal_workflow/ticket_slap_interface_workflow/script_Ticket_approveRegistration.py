ticket = state_change["object"]
from DateTime import DateTime

portal = context.getPortalObject()

if ticket.getSimulationState() != "draft":
  return

if ticket.getReference() in [None, ""]:
  raise ValueError("Reference is missing on the Ticket")

# Get the user id of the context owner.
local_role_list = ticket.get_local_roles()
for group, role_list in local_role_list:
  if 'Owner' in role_list:
    user_id = group
    break

person = portal.portal_catalog.getResultValue(user_id=user_id)
if person is None:
  # Value was created by super user, so there isn't a point on continue
  return

# XXX unhardcode the trade condition, by adding a preference
if ticket.getSpecialise() != "sale_trade_condition_module/slapos_ticket_trade_condition":
  return

trade_condition = portal.sale_trade_condition_module.slapos_ticket_trade_condition

ticket.edit(
  source_section=trade_condition.getSourceSection(),
  source_trade=trade_condition.getSourceSection(),
  source=trade_condition.getSource())

ticket.setStartDate(DateTime())

ticket.requestEvent(
  event_title=ticket.getTitle(),
  event_content=ticket.getDescription(),
  event_source=ticket.getDestinationDecision()
)

event_relative_url = context.REQUEST.get("event_relative_url")
ticket.setCausality(event_relative_url)
