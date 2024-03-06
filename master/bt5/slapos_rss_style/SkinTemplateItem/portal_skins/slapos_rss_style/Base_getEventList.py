"""Returns all ticket related events for RSS
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

if follow_up_portal_type is None:
  follow_up_portal_type = ['Support Request', 'Regularisation Request', 'Upgrade Decision']

ticket_simulation_state = [
  'validated','submitted', 'suspended', 'invalidated',
  # Unfortunally Upgrade decision uses diferent states.
  'confirmed', 'started', 'stopped', 'delivered'
]

context_kw = {}
if context_related:
  context_kw['follow_up__uid'] = [x.getUid() for x in portal.portal_catalog(
    causality__uid=context.getUid(),
    portal_type=follow_up_portal_type,
    simulation_state=ticket_simulation_state
  )] or [-1]
else:
  context_kw['follow_up__simulation_state'] = ticket_simulation_state
  context_kw['follow_up__portal_type'] = follow_up_portal_type

data_list = []
for brain in portal.portal_simulation.getMovementHistoryList(
    security_query=portal.portal_catalog.getSecurityQuery(),
    # Limit only to listable portal types
    portal_type=['Web Message', 'Mail Message'],
    only_accountable=False,
    simulation_state=('started', 'stopped', 'delivered'),
    limit=list_lines,
    sort_on=(('stock.date', 'desc'),
             ('uid', 'desc')),
    **context_kw):
  event = brain.getObject()

  (ticket_title,
   ticket_category,
   ticket_link) = getTicketInfo(event)

  data_list.append(
      Object(**{
        'title': ticket_title,
        'category': ticket_category,
        'author': event.getSourceTitle(checked_permission="View"),
        'link': ticket_link,
        'description': event.getTextContent(),
        'pubDate': event.getStartDate(),
        'guid': '{}-{}'.format(
                  event.getFollowUp(),
                  event.getRelativeUrl()),
        'thumbnail': ( None)
        })
      )

return data_list
