from Products.ZSQLCatalog.SQLCatalog import Query, SimpleQuery, NegatedQuery, ComplexQuery

portal = context.getPortalObject()
error_list = []

catalog_query_kw = {
  "creation_date" : None,
  "select_list" : {"creation_date": None},
  "query": ComplexQuery(
    Query(portal_type=('Software Instance', 'Slave Instance', 'Compute Node', 'Compute Partition'),
          validation_state=('validated', 'invalidated'),),
    ComplexQuery(
          SimpleQuery(portal_type=('Sale Order',)),
          NegatedQuery(SimpleQuery(simulation_state='draft')),
          logical_operator='AND'),
    logical_operator='OR')
}

required_to_reindex = portal.portal_catalog.countResults(**catalog_query_kw)[0][0]

if required_to_reindex:
  error_list.append('There are %s documents that require reindex due "None" creation date' % (required_to_reindex))
  if fixit:
    tag = 'update_none_creation_date_from_large_workflow_histories'
    portal.portal_catalog.activate(tag=tag, activity='SQLQueue').searchAndActivate(
      activate_kw={'tag': tag, 'priority': 6},
      method_id='reindexObject',
      **catalog_query_kw
    )
return error_list
