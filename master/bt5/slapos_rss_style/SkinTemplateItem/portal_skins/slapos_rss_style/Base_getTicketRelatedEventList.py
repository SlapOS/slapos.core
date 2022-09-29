"""Returns all ticket related events for RSS from a given module
"""
from Products.PythonScripts.standard import Object
portal = context.getPortalObject()

# for safety, we limit at 100 lines
list_lines = min(list_lines, 100)

getTicket_memo = {}
def getTicketInfo(event):
  follow_up = event.getFollowUp()
  try:
    return getTicket_memo[follow_up]
  except KeyError:
    ticket = portal.restrictedTraverse(follow_up, None)
    if ticket is None:
      # For corner cases where user has an event for which he cannot access the ticket,
      # we don't raise error so that others events are visible.
      return event.getTitle(), '', ''
    getTicket_memo[follow_up] = (
      ticket.getTitle(),
      ticket.getResourceTranslatedTitle() or '',
      ticket.Base_getTicketUrl(),
    )
    return getTicket_memo[follow_up]

data_list = []

for brain in portal.portal_simulation.getMovementHistoryList(
    security_query=portal.portal_catalog.getSecurityQuery(),
    # Limit only to listable portal types
    portal_type=['Web Message', 'Mail Nessage'],
    follow_up_default_or_child_aggregate_uid=context.getUid(),
    follow_up_simulation_state = ['validated','submitted', 'suspended', 'invalidated', 
                                  # Unfortunally Upgrade decision uses diferent states.
                                  'confirmed', 'started', 'stopped', 'delivered'],
    only_accountable=False,
    # Only query by portal types of the module
    follow_up_portal_type=["Support Request", "Upgrade Decision"],
    omit_input=True,
    simulation_state=('started', 'stopped', 'delivered'),
    limit=list_lines,
    sort_on=(('stock.date', 'desc'),
             ('uid', 'desc')),):
  event = brain.getObject()
  (ticket_title,
   ticket_category,
   ticket_link) = getTicketInfo(event)

  data_list.append(
      Object(**{
        'title': ticket_title,
        'category': ticket_category,
        'author': brain.node_title,
        'link': ticket_link,
        'description': event.Event_getRSSTextContent(),
        'pubDate': brain.date,
        'guid': '{}-{}'.format(
                  event.getFollowUp(),
                  event.getRelativeUrl()),
        'thumbnail': ( None)
        })
      )

return data_list
