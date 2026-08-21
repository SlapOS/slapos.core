from Products.ZSQLCatalog.SQLCatalog import SimpleQuery, ComplexQuery

portal = context.getPortalObject()
monitor_enabled_category = portal.restrictedTraverse(
  "portal_categories/monitor_scope/enabled", None)
priority = 4

portal = context.getPortalObject()
portal.portal_catalog.searchAndActivate(
    validation_state='validated',
    method_id='ComputeNode_checkProjectMontoringState',
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
    method_kw={'tag': tag, 'priority': priority},
  activate_kw={'tag': tag, 'priority': priority}
  )
context.activate(after_tag=tag).getId()
