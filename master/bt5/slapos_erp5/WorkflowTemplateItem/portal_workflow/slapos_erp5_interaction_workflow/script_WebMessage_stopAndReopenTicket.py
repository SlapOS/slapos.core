web_message = state_object["object"]
portal = context.getPortalObject()
person = portal.portal_membership.getAuthenticatedMember().getUserValue()

if person is None:
  return

if web_message.getSimulationState() != "draft":
  return

if not web_message.hasStartDate():
  web_message.setStartDate(DateTime())

# The user isn't the customer, so it is not comming from the user
# interface.
ticket = web_message.getFollowUpValue()
if ticket.getDestinationDecision() != person.getRelativeUrl():
  return

# The user isn't the sender, so it is not comming from UI, but from
# an alarm.
source = web_message.getSource()
if source != person.getRelativeUrl():
  return

edit_kw = {"content_type":"text/plain"}
# Copy destination and resource from ticket.
if web_message.getDestination() is None:
  edit_kw["destination"] = ticket.getSource()

if web_message.getResource() is None:
  edit_kw["resource"] = ticket.getResource()

web_message.edit(**edit_kw)

web_message.stop(comment="Submitted from the renderjs app")
if portal.portal_workflow.isTransitionPossible(ticket, "validate"):
  ticket.validate(comment="See %s" % web_message.getRelativeUrl())
