# -*- coding: utf-8 -*-
"""
  Returns all ticket related events for RSS
"""
from Products.PythonScripts.standard import Object
from Products.ZSQLCatalog.SQLCatalog import SimpleQuery
from DateTime import DateTime
from erp5.component.module.DateUtils import addToDate
portal = context.getPortalObject()
now = DateTime()

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
      return event.getTitle(), '', '', ''

    if ticket.getSimulationState() == 'suspended':
      ticket_emoji = '❓ '
    elif ticket.getSimulationState() in ['delivered', 'invalidated', 'cancelled', 'accepted', 'rejected']:
      ticket_emoji = ''
    elif (ticket.getSimulationState() in ['submitted']) and (ticket.getResource('') != 'service_module/slapos_crm_monitoring'):
      # Display a bell for submitted ticket created by customers
      ticket_emoji = '🔔 '
    else:
      ticket_emoji = '🚧 '
    getTicket_memo[follow_up] = (
      ticket.getTitle(),
      # Do not show monitoring resource, to reduce the text density
      ticket.getResourceTranslatedTitle() or '' if (ticket.getResource('') != 'service_module/slapos_crm_monitoring') else '',
      web_site.absolute_url() + "/#/" + ticket.getRelativeUrl(),
      ticket_emoji
    )
    return getTicket_memo[follow_up]

follow_up_portal_type = ['Support Request', 'Regularisation Request',
                         'Upgrade Decision', 'Subscription Request']

data_list = []
for brain in portal.portal_catalog(
    # Limit only to listable portal types
    portal_type=['Web Message', 'Mail Message'],
    simulation_state=('started', 'stopped', 'delivered'),
    limit=list_lines,
    sort_on=(('delivery.start_date', 'desc'),
             ('uid', 'desc')),
    follow_up__portal_type=follow_up_portal_type,
    # Limit the number of checked entries
    # to speed up the sorting
    # 1 month, because some tickets are automatically closed after 1 month
    **{
      'delivery.start_date': SimpleQuery(
        comparison_operator=">=",
        **{'delivery.start_date': addToDate(now, {'month': -1})}
      )
    }
):
  event = brain.getObject()

  (ticket_title,
   ticket_category,
   ticket_link,
   ticket_emoji) = getTicketInfo(event, web_site)

  data_list.append(
      Object(**{
        'title': context.Base_convertToSafeXML(
          "%s%s%s" % (ticket_emoji, '[%s] ' % ticket_category.upper() if ticket_category else '', ticket_title)),
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
