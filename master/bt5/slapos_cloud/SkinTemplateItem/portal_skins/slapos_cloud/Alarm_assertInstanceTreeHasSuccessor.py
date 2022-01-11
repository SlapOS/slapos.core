portal = context.getPortalObject()
from Products.ZSQLCatalog.SQLCatalog import SimpleQuery, NegatedQuery

portal.portal_catalog.searchAndActivate(
  portal_type='Instance Tree',
  validation_state='validated',
  related_successor_but_with_different_title_than_catalog_title="%",
  successor_title=NegatedQuery(SimpleQuery(successor_title=None, comparison_operator='is')),
  method_id='InstanceTree_assertSuccessor',
  activate_kw={'tag': tag})

# Instance tree without any Software Instance
select_dict= {'successor__uid': None}
portal.portal_catalog.searchAndActivate(
  portal_type='Instance Tree',
  validation_state='validated',
  method_id='InstanceTree_assertSuccessor',
  activate_kw={'tag': tag},
  left_join_list=select_dict.keys(),
  **select_dict
)

context.activate(after_tag=tag).getId()
