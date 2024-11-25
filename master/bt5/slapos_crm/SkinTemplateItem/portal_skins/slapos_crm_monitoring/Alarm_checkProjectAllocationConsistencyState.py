from Products.ZSQLCatalog.SQLCatalog import SimpleQuery, ComplexQuery

portal = context.getPortalObject()
monitor_enabled_category = portal.restrictedTraverse(
  "portal_categories/monitor_scope/enabled", None)

portal = context.getPortalObject()
portal.portal_catalog.searchAndActivate(
    validation_state='validated',
    method_id='ComputeNode_checkProjectAllocationConsistencyState',
    node=ComplexQuery(
        SimpleQuery(portal_type='Compute Node'),
        SimpleQuery(monitor_scope__uid=monitor_enabled_category.getUid()),
        logical_operator='and'
    ),
    group_by=['follow_up_uid'],
    method_kw={'tag': tag},
  activate_kw={'tag': tag, 'priority': 2}
  )
context.activate(after_tag=tag).getId()
