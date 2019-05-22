from Products.ZSQLCatalog.SQLCatalog import Query, NegatedQuery
portal = context.getPortalObject()
return portal.portal_catalog(
    portal_type="Hosting Subscription",
    validation_state="validated",
    query=NegatedQuery(Query(aggregate_related_portal_type="Subscription Request")),
    **kw)
