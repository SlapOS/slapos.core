portal = context.getPortalObject()
result_list = []

migration_kw = {
  'portal_type': 'Computer Consumption TioXML File',
}

non_migrated_instance = portal.portal_catalog(
  limit=1,
  sort_on=[['indexation_timestamp', 'ASC']],
  **migration_kw
)

if (len(non_migrated_instance) == 1) and ('slapos_consumption_document_workflow' not in non_migrated_instance[0].workflow_history):
  result_list.append("all X needs updates %s" % non_migrated_instance[0].getRelativeUrl())
  if fixit:
    tag = script.getId()
    portal.portal_catalog.searchAndActivate(
      activate_kw=dict(priority=5, tag=tag),
      method_kw={'fixit': True},
      method_id='ComputerConsumptionTioXMLFile_checkWorkflowHistoryMigrationConsistency',
      **migration_kw)
return result_list
