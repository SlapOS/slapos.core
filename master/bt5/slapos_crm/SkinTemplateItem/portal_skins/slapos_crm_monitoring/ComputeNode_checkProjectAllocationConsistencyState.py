from Products.ZSQLCatalog.SQLCatalog import SimpleQuery, ComplexQuery

portal = context.getPortalObject()
monitor_enabled_category = portal.restrictedTraverse(
  "portal_categories/monitor_scope/enabled", None)

project = context.getFollowUpValue(portal_type='Project')
assert project is not None

if project.Project_isSupportRequestCreationClosed():
  return

if monitor_enabled_category is not None:
  project_uid = project.getUid()
  portal.portal_catalog.searchAndActivate(
    node=ComplexQuery(
      SimpleQuery(portal_type='Remote Node'),
      ComplexQuery(
        SimpleQuery(portal_type='Compute Node'),
        SimpleQuery(monitor_scope__uid=monitor_enabled_category.getUid()),
        logical_operator='and'
      ),
      logical_operator='or'
    ),
    validation_state='validated',
    follow_up__uid=project_uid,
    method_id='ComputeNode_checkAllocationConsistencyState',
    # This alarm bruteforce checking all documents,
    # without changing them directly.
    # Increase priority to not block other activities
    activate_kw=activate_kw
  )
