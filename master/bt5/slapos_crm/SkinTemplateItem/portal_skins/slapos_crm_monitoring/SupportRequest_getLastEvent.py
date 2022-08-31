portal = context.getPortalObject()
return portal.portal_catalog.getResultValue(
             title=title,
             follow_up_uid=context.getUid(),
             portal_type=portal.getPortalEventTypeList(),
             sort_on=[('delivery.start_date', 'DESC')])
