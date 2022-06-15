portal = context.getPortalObject()
return portal.portal_catalog.getResultValue(
             title={'query': title, 'key': 'ExactMatch'},
             follow_up__uid=context.getUid(),
             portal_type=portal.getPortalEventTypeList(),
             sort_on=[('delivery.start_date', 'DESC')])
