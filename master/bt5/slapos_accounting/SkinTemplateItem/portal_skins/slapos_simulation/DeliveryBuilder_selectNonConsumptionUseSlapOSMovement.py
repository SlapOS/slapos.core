from Products.ZSQLCatalog.SQLCatalog import SimpleQuery, NegatedQuery, ComplexQuery
select_dict = {'delivery_uid': None}
kw['select_dict']=select_dict
kw['left_join_list']=select_dict.keys()
kw['delivery_uid']=None
kw['group_by']=('uid',)

portal = context.getPortalObject()
kw['portal_type'] = 'Simulation Movement'
kw['ledger__uid'] = portal.portal_categories.ledger.automated.getUid()

# Do not select consumption, since they use a specific builder for it.
kw['strict_use_uid'] = ComplexQuery(
  NegatedQuery(SimpleQuery(strict_use_uid=portal.portal_categories.use.trade.consumption.getUid())),
  SimpleQuery(strict_use_uid=None),
  logical_operator='or'
)

if src__ == 0:
  return portal.portal_catalog(**kw)
else:
  return portal.portal_catalog(src__=1, **kw)
