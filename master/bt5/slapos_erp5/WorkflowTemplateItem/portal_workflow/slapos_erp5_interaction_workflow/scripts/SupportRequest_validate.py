"""
  Open the ticket
"""
ticket = state_object["object"]
if ticket.getSimulationState() != "draft":
  return

ticket.validate()
