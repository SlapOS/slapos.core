from json import dumps

attention_point_list = []
portal = context.getPortalObject()

def addAttentionForTicket(ticket):
  msg = None
  if ticket.getPortalType() == "Support Request":
    msg = context.Base_translateString("Ticket waiting your response")

  elif ticket.getPortalType() == "Upgrade Decision":
    msg = context.Base_translateString("Please Upgrade this service")

  elif ticket.getPortalType() == "Regularisation Request":
    msg = context.Base_translateString(
      "Regularisation waiting your response")

  if msg:
    return {"text": msg, "link": ticket.getRelativeUrl()}


# Display unresponded tickets on services or servers
if context.getPortalType() in ["Hosting Subscription", "Computer"]:
  simulation_state = ["suspended", "confirmed"]
  for ticket in context.Base_getOpenRelatedTicketList(
   limit=3, simulation_state=simulation_state):
    entry = addAttentionForTicket(ticket)
    if entry is not None:
      attention_point_list.append(entry)
      
# This is a limitation of the API that will consider that all tickets
# Are from this module
if context.getPortalType() in ["Support Request Module"]:
  simulation_state = ["suspended", "confirmed"]
  person = portal.portal_membership.getAuthenticatedMember().getUserValue()
  for ticket in portal.portal_catalog(
    portal_type=("Support Request", "Upgrade Decision", "Regularisation Request"),
    destination_decision_uid=person.getUid(),
    limit=3, simulation_state=simulation_state):

    entry = addAttentionForTicket(ticket)
    if entry is not None:
      attention_point_list.append(entry)
      
return dumps(attention_point_list)
