select_dict= {'delivery_uid': None}
kw['select_dict']=select_dict
kw['left_join_list']=select_dict.keys()
kw['delivery_uid']=None
kw['group_by']=('uid',)

portal = context.getPortalObject()
kw['ledger__uid'] = portal.portal_categories.ledger.automated.getUid()
if src__==0:
  return portal.portal_catalog(**kw)
else:
  return portal.portal_catalog(src__=1, **kw)
