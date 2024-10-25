"""
  Returns all ticket related events for RSS
"""
from Products.PythonScripts.standard import Object
portal = context.getPortalObject()

# for safety, we limit at 100 lines
list_lines = min(list_lines, 100)

web_site =  context.getWebSiteValue()
if not web_site:
  web_site = context.getPortalObject()

getTicket_memo = {}
def getTicketInfo(event, web_site):
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
      web_site.absolute_url() + "/#/" + ticket.getRelativeUrl(),
    )
    return getTicket_memo[follow_up]

follow_up_portal_type = ['Support Request', 'Regularisation Request',
                         'Upgrade Decision', 'Subscription Request']

follow_up_simulation_state = [
  'validated','submitted', 'suspended', 'invalidated',
  # Unfortunally Upgrade decision uses diferent states.
  'confirmed', 'started', 'stopped', 'delivered'
]

data_list = []
for brain in portal.portal_catalog(
    # Limit only to listable portal types
    portal_type=['Web Message', 'Mail Message'],
    simulation_state=('started', 'stopped', 'delivered'),
    limit=list_lines,
    sort_on=(('stock.date', 'desc'),
             ('uid', 'desc')),
    follow_up__simulation_state=follow_up_simulation_state,
    follow_up__portal_type=follow_up_portal_type):
  event = brain.getObject()

  (ticket_title,
   ticket_category,
   ticket_link) = getTicketInfo(event, web_site)

  data_list.append(
      Object(**{
        'title': context.Base_convertToSafeXML(
          "[%s] %s" % (ticket_category.upper(), ticket_title)),
        'category': ticket_category,
        'author':  context.Base_convertToSafeXML(
          event.getSourceTitle(checked_permission="View")),
        'link': ticket_link,
        'description':  context.Base_convertToSafeXML(event.getTextContent()),
        'pubDate': event.getStartDate(),
        'guid': '{}-{}'.format(
                  event.getFollowUp(),
                  event.getRelativeUrl()),
        'thumbnail': ( None)
        })
      )

return data_list
