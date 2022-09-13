from Products.ZSQLCatalog.SQLCatalog import ComplexQuery, SimpleQuery

portal = context.getPortalObject()
person_uid = context.getUid()

query = ComplexQuery(
  ComplexQuery(
    SimpleQuery(portal_type=["Support Request", "Regularisation Request"]),
    SimpleQuery(simulation_state="suspended"),
    SimpleQuery(destination_decision_uid=person_uid),
    logical_operator='and'),
  ComplexQuery(
    SimpleQuery(portal_type="Upgrade Decision"),
    SimpleQuery(simulation_state="confirmed"),
    SimpleQuery(destination_decision_uid=person_uid),
    logical_operator='and'),
  logical_operator='or')

return portal.portal_catalog(query=query, **kw)
