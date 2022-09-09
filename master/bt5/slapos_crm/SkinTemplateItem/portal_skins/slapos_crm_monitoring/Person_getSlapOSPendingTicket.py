from Products.ZSQLCatalog.SQLCatalog import ComplexQuery, SimpleQuery

portal = context.getPortalObject()

query = ComplexQuery(
  ComplexQuery(
    SimpleQuery(portal_type=["Support Request", "Regularisation Request"]),
    SimpleQuery(simulation_state="suspended"),
    logical_operator='and'),
  ComplexQuery(
    SimpleQuery(portal_type="Upgrade Decision Line"),
    SimpleQuery(simulation_state="confirmed"),
    logical_operator='and'),
  logical_operator='or')

return portal.portal_catalog(query=query, **kw)
