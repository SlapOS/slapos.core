from DateTime import DateTime
from Products.ZSQLCatalog.SQLCatalog import Query, ComplexQuery

portal = context.getPortalObject()

max_date = DateTime()

query_list = [
  Query(parent_uid=portal.software_instance_module.getUid()),
  Query(validation_state='validated')
]

min_date = min(context.getEffectiveDate() or max_date, max_date)

if min_date == max_date:
  time_query = ComplexQuery(
    Query(**{'versioning.expiration_date': None}),
    Query(**{'versioning.expiration_date': {'query':max_date, 'range': 'ngt'}}),
    logical_operator='OR'
  )
else:
  time_query = ComplexQuery(
    Query(**{'versioning.expiration_date': None}),
    ComplexQuery(
      Query(**{'versioning.expiration_date': {'query':max_date, 'range': 'ngt'}}),
      Query(**{'versioning.expiration_date': {'query':min_date, 'range': 'nlt'}}),
      logical_operator='AND'
    ),
    logical_operator='OR'
  )

query_list.append(time_query)

portal.portal_catalog.searchAndActivate(
  query=ComplexQuery(logical_operator='AND', *query_list),
  method_id='Base_generateConsumptionDeliveryForValidatedInstance',
  packet_size=1,
  activate_kw={'tag': tag}
)

context.setEffectiveDate(max_date)

context.activate(after_tag=tag).getId()
