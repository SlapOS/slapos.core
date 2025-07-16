from DateTime import DateTime
from Products.ZSQLCatalog.SQLCatalog import Query, ComplexQuery

portal = context.getPortalObject()

now = DateTime()
check_date = min(context.getEffectiveDate() or now, now)

query_list = [
  Query(parent_uid=portal.software_instance_module.getUid()),
  Query(validation_state='invalidated'),
  ComplexQuery(Query(**{'versioning.expiration_date': None}),
               Query(**{'versioning.expiration_date': {'query':check_date, 'range': 'nlt'}}),
               logical_operator='OR')
]

portal.portal_catalog.searchAndActivate(
  query=ComplexQuery(logical_operator='AND', *query_list),
  method_id='Base_generateConsumptionDeliveryForInvalidatedInstance',
  packet_size=1,
  activate_kw={'tag': tag}
)
context.setEffectiveDate(now)


context.activate(after_tag=tag).getId()
