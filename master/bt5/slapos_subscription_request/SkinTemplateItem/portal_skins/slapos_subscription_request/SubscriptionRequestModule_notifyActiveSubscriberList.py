from DateTime import DateTime
portal = context.getPortalObject()

# Notify users with active instances.
ticket_list = []
person_notification_list = []
for subscription_request in portal.subscription_request_module.searchFolder(
    portal_type="Subscription Request"):
  hosting_subscription = subscription_request.getAggregateValue()
  if hosting_subscription is None or \
       hosting_subscription.getSlapState() == "destroy_requested":
    continue

  person_notification_list.append(subscription_request.getDestinationSectionValue())


for destination_decision_value in list(set(person_notification_list)):
  support_request_in_progress = portal.portal_catalog.getResultValue(
    portal_type = 'Support Request',
    title = title,
    simulation_state = ["validated", "submitted", "suspended"],
    default_destination_decision_uid = destination_decision_value.getUid())

  if support_request_in_progress is not None:
    return support_request_in_progress

  support_request_in_progress = context.REQUEST.get(
    "support_request_in_progress_%s" % destination_decision_value.getUid(), None)

  if support_request_in_progress is not None:
    raise ValueError("There is one ticket in progress for the %s: %s" %
                      (destination_decision_value.getRelativeUrl(),
                       support_request_in_progress))

  # This might be a bit hard to keep the usage of the template since
  # we could like to make ticket portal type selectable.
  ticket = portal.restrictedTraverse(
          portal.portal_preferences.getPreferredSupportRequestTemplate())\
           .Base_createCloneDocument(batch_mode=1)

  ticket.edit(
      title = title,
      description=text_content,
      start_date = start_date,
      destination_decision_value=destination_decision_value,
      source=source,
      resource=resource)

  # Keep on draft for review before send
  if simulation_state == "validated":
    ticket.validate()
  elif simulation_state == "invalidated":
    ticket.validate()
    ticket.invalidate()
  elif simulation_state == "suspended":
    ticket.validate()
    ticket.suspend()

  context.REQUEST.set(
    "support_request_in_progress_%s" % destination_decision_value.getUid(),
    ticket.getRelativeUrl())

  event = portal.event_module.newContent(
    portal_type=portal_type)

  ticket.edit(causality_value=event)
  # Copy original post into the original message.
  event.edit(
    title=ticket.getTitle(),
    text_content=text_content,
    source=source,
    destination=ticket.getDestinationDecision())

  # Move state before setFollowUp
  if send_event:
    event.start(comment="Automatic sending notification for the subscriber")
  else:
    event.plan(comment="Planned to send later")

  ticket_list.append(ticket)

if ticket_list:
  return ticket.getParentValue().Base_redirect(
    keep_items={"portal_message_status": "Ticket Created.",
                "uid": [i.getUid() for i in ticket_list]})

return context.Base_redirect(
    keep_items={"portal_message_status": "No Ticket Created."})
