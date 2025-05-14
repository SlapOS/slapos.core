from Products.ZSQLCatalog.SQLCatalog import SimpleQuery, ComplexQuery

portal = context.getPortalObject()
monitor_enabled_category = portal.restrictedTraverse(
  "portal_categories/monitor_scope/enabled", None)

portal = context.getPortalObject()
activate_kw = {'tag': tag, 'priority': 5}
portal.portal_catalog.searchAndActivate(
    validation_state='validated',
    method_id='ComputeNode_checkProjectAllocationConsistencyState',
    node=ComplexQuery(
      SimpleQuery(portal_type='Remote Node'),
      ComplexQuery(
        SimpleQuery(portal_type='Compute Node'),
        SimpleQuery(monitor_scope__uid=monitor_enabled_category.getUid()),
        logical_operator='and'
      ),
      logical_operator='or'
    ),
    group_by=['follow_up_uid'],
    method_kw={'activate_kw': activate_kw},
  activate_kw=activate_kw
  )
context.activate(after_tag=tag).getId()
