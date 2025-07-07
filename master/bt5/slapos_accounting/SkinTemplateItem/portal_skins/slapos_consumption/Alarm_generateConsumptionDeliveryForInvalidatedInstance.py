from DateTime import DateTime
from Products.ZSQLCatalog.SQLCatalog import Query, ComplexQuery


portal = context.getPortalObject()

check_modification_date_max = DateTime()

query_list = [
  Query(parent_uid=portal.software_instance_module.getUid()),
  Query(validation_state='invalidated'),
  Query(**{'modification_date': {'query':check_modification_date_max, 'range': 'ngt'}})
]

check_modification_date_min = context.getEffectiveDate()

if check_modification_date_min:
  query_list.append(Query(**{'modification_date': {'query':check_modification_date_min, 'range': 'nlt'}}))

context.setEffectiveDate(check_modification_date_max)




portal.portal_catalog.searchAndActivate(
  query=ComplexQuery(logical_operator='AND', *query_list),
  method_id='Base_generateConsumptionDeliveryForInvalidatedInstance',
  packet_size=1,
  activate_kw={'tag': tag}
)

context.activate(after_tag=tag).getId()
