event = context

if event.getSimulationState() != 'stopped':
  return

ticket = event.getFollowUpValue(portal_type='Upgrade Decision')
if ticket is None:
  # No ticket, don't try doing anything
  return

simulation_state = ticket.getSimulationState()
if simulation_state not in ['delivered', 'rejected', 'cancelled']:
  # Only deliver after ticket is closed.
  return

comment = 'Ticket was %s' % simulation_state
event.deliver(comment=comment)
event.reindexObject(activate_kw=activate_kw)
