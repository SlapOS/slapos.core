event = context

if event.getSimulationState() != 'stopped':
  return

ticket = event.getFollowUpValue(portal_type='Subscription Request')
if ticket is None:
  # No ticket, don't try doing anything
  return

if ticket.getSimulationState() != 'invalidated':
  # Only deliver after ticket is closed.
  return

comment = 'Ticket was invalidated'
event.deliver(comment=comment)
event.reindexObject(activate_kw=activate_kw)
