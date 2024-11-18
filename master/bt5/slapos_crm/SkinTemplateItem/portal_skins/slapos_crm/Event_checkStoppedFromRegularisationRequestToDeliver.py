event = context

if event.getSimulationState() != 'stopped':
  return

ticket = event.getFollowUpValue(portal_type='Regularisation Request')
if ticket is None:
  # No ticket, don't try doing anything
  return

if ticket.getSimulationState() not in ['invalidated', 'validated']:
  # Do nothing for suspended tickets
  return
comment = 'Ticket was %s' % ticket.getSimulationState()
is_event_older_than_ticket_modification = (event.getCreationDate() <= ticket.getModificationDate())

if not is_event_older_than_ticket_modification:
  comment = 'Ticket has been modified'
  ticket.edit(activate_kw=activate_kw)

event.deliver(comment=comment)
event.reindexObject(activate_kw=activate_kw)
