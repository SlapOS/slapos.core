portal = context.getPortalObject()
from Products.ZSQLCatalog.SQLCatalog import SimpleQuery, NegatedQuery

# XXX TODO this is really not efficient
# this does not scale with millions of uid
# how to use a left join instead? or a single query with the embedded subquery?
subscribed_uid_list = [x.uid for x in portal.portal_catalog(
  portal_type=["Compute Node", "Instance Tree"],
  aggregate__related__portal_type="Subscription Request"
)]

sql_kw = {}
if subscribed_uid_list:
  # Use 'catalog.uid', because searchAndActivate will use 'uid' to order the
  # results and iterate other them
  sql_kw['catalog.uid'] = NegatedQuery(SimpleQuery(uid=subscribed_uid_list))
portal.portal_catalog.searchAndActivate(
  method_id='Item_createSubscriptionRequest',
  portal_type=["Compute Node", "Instance Tree"],
  validation_state="validated",
  packet_size=1, # Separate calls to many transactions
  activate_kw={'tag': tag},
  method_kw={'activate_kw': {'tag': tag}},
  **sql_kw
)
"""
# XXX if there is a non Subscription Request with such aggregate link
# it will lead to not creating the Subscription Request
# TODO find a way to check the portal type
select_dict= {'aggregate__related__uid': None}
kw = {}
kw['select_dict'] = select_dict
kw['left_join_list'] = select_dict.keys()
kw.update(select_dict)

portal.portal_catalog.searchAndActivate(
  method_id='Item_createSubscriptionRequest',
  # Project are created only from UI for now
  portal_type=["Instance Tree", "Compute Node"],
  activate_kw={'tag': tag},
  **kw
)
"""
context.activate(after_tag=tag).getId()
