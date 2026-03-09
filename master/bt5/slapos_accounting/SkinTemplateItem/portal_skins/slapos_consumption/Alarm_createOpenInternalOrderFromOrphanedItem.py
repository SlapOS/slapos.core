portal = context.getPortalObject()
from Products.ZSQLCatalog.SQLCatalog import SimpleQuery, NegatedQuery

portal_type = ["Compute Node", "Software Instance", "Slave Instance"]
# XXX TODO this is really not efficient
# this does not scale with millions of uid
# how to use a left join instead? or a single query with the embedded subquery?
subscribed_uid_list = [x.uid for x in portal.portal_catalog(
  portal_type=portal_type,
  validation_state="validated",
  aggregate__related__portal_type="Open Internal Order Line"
)]

sql_kw = {}
if subscribed_uid_list:
  # Use 'catalog.uid', because searchAndActivate will use 'uid' to order the
  # results and iterate other them
  sql_kw['catalog.uid'] = NegatedQuery(SimpleQuery(uid=subscribed_uid_list))
portal.portal_catalog.searchAndActivate(
  method_id='Item_createOpenInternalOrder',
  portal_type=portal_type,
  validation_state="validated",
  packet_size=1, # Separate calls to many transactions
  activate_kw={'tag': tag, 'priority': 2},
  method_kw={'activate_kw': {'tag': tag, 'priority': 2}},
  **sql_kw
)

context.activate(after_tag=tag).getId()
