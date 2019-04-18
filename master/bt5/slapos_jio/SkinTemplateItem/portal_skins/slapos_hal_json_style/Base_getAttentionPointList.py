from json import dumps

attention_point_list = []

# For now keep the logic here hardcoded.
if context.getPortalType() == "Hosting Subscription":
  simulation_state = ["suspended", "confirmed"]
  for ticket in context.Base_getOpenRelatedTicketList(
   limit=3, simulation_state=simulation_state):
    if ticket.getPortalType() == "Support Request":
      attention_point_list.append(
        {"text": "Ticket waiting your response",
         "link": ticket.getRelativeUrl()})
    elif ticket.getPortalType() == "Upgrade Decision":
      attention_point_list.append(
        {"text": "Please Upgrade this service",
         "link": ticket.getRelativeUrl()})

return dumps(attention_point_list)
