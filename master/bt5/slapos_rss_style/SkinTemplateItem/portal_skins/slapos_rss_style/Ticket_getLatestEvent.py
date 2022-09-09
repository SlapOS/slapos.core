from Products.ERP5Type.Cache import CachingMethod
portal = context.getPortalObject()

def getLastEventRelativeUrl(uid):
  portal = context.getPortalObject()
  last_event = portal.portal_catalog.getResultValue(
    follow_up_uid=context.getUid(),
    portal_type=portal.getPortalEventTypeList(),
    simulation_state=["confirmed", "started", "stopped", "delivered"],
    sort_on=(("modification_date", 'DESC'),))

  if last_event is not None:
    return last_event.getRelativeUrl()
  else:
    return last_event

last_event_url = CachingMethod(getLastEventRelativeUrl,
        id='Ticket_getLatestEventRelativeUrl',
        cache_factory='erp5_content_short')(context.getUid())

if last_event_url is not None:
  return portal.restrictedTraverse(last_event_url)
