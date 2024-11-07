event = context

if event.getSimulationState() != 'stopped':
  return

support_request = event.getFollowUpValue(portal_type=['Support Request', 'Regularisation Request'])
if support_request is None:
  # No ticket, don't try doing anything
  return

is_event_older_than_ticket_modification = (event.getCreationDate() <= support_request.getModificationDate())

if is_event_older_than_ticket_modification:
  if support_request.getSimulationState() in ['invalidated', 'validated']:
    # If invalidated, Ticket reach final state close all previous events
    # If validated or suspended, close events w/o edit the ticket.
    event.deliver(comment='Ticket was %s' % support_request.getSimulationState())
    event.reindexObject(activate_kw=activate_kw)
  return
else:
  if support_request.getSimulationState() == 'validated':
    # Event is more recent than the ticket
    # Touch the ticket, to allow manager to see it as recent
    # and deliver the event
    support_request.edit(activate_kw=activate_kw)
    event.deliver(comment='Ticket has been modified')
    event.reindexObject(activate_kw=activate_kw)
    return

  if support_request.getSimulationState() == 'invalidated':
    # Event is more recent than the ticket reopen the ticket
    # and deliver the event.
    support_request.validate(activate_kw=activate_kw)
    event.deliver(comment='Ticket has been revalidated')
    event.reindexObject(activate_kw=activate_kw)
    return
