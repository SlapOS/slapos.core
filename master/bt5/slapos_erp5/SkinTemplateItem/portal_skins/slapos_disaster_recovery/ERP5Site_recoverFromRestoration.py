portal = context.getPortalObject()

now = DateTime()
before = now - int(7)

strfstring = '%Y-%m-%d %H:%M:%S'

portal.ERP5Site_checkLatestModifiedDocumentList(0, 1000, 100, before.strftime(strfstring), now.strftime(strfstring))

# Force reindexation of recently created document
# This expect module to use HBTree
for module_id in portal.objectIds(("ERP5 Folder",)):
  if module_id.endswith("_module"):
    portal[module_id].recurseCallMethod(
      'recursiveReindexObject',
      max_depth=1,
      min_depth=1,
      max_retry=0,
      activity_count=100,
      min_id=before.strftime("%Y%m%d"),
    )

portal.ERP5Site_checkDeletedDocumentList(0, 1000, 100)

for module_id in [
  'portal_preferences',
  'portal_categories',
  'portal_alarms',
  'portal_simulation']+portal.objectIds(("ERP5 Folder",)):
  portal[module_id].recurseCallMethod(
    'immediateReindexObject',
    min_depth=1,
    max_depth=10000,
    activate_kw=dict(
      group_method_id='portal_catalog/catalogObjectList',
      alternate_method_id='alternateReindexObject',
      group_method_cost=1,
      priority=6,
    ),
    max_retry=0,
    activity_count=100,
  )

return "OK"
