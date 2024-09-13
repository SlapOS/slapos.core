from Products.ZSQLCatalog.SQLCatalog import SimpleQuery
portal = context.getPortalObject()
support_request = context

any_recent_event = portal.portal_catalog.getResultValue(
  portal_type=portal.getPortalEventTypeList(),
  follow_up__uid=support_request.getUid(),
  creation_date=SimpleQuery(creation_date=support_request.getModificationDate(), comparison_operator='>')
)
if any_recent_event is not None:
  support_request.validate(comment='Reopened because %s is newer' % any_recent_event.getRelativeUrl())
  support_request.reindexObject(activate_kw=activate_kw)
