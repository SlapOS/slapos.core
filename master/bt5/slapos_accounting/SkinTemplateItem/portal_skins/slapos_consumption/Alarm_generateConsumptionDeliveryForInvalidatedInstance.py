from Products.ZSQLCatalog.SQLCatalog import Query,ComplexQuery

portal = context.getPortalObject()


query_list = [
  Query(parent_uid=portal.software_instance_module.getUid()),
  Query(validation_state='invalidated'),
  Query(**{'versioning.expiration_date': None})
]

portal.portal_catalog.searchAndActivate(
  query=ComplexQuery(logical_operator='AND', *query_list),
  method_id='Base_generateConsumptionDeliveryForInvalidatedInstance',
  packet_size=1,
  activate_kw={'tag': tag}
)


context.activate(after_tag=tag).getId()
