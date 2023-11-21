portal = context.getPortalObject()

tag = script.id
migrated_select_dict={'follow_up__uid': '%'}

############################################
# Delete all object to drop
############################################
packet_kw = {
  'activate_kw': {'tag': tag},# 'serialization_tag': tag},
  'packet_size': 1, # Separate calls to many transactions (calculation can take time)
  'activity_count': 1000,
}
portal.portal_catalog.searchAndActivate(
  method_id='Base_deleteProcessedDocumentDuringPurge',
  portal_type=["Internal Packing List"],
  **packet_kw
)

# Delete existing old product only
if portal.portal_catalog.getResultValue(portal_type="Software Release") is not None:
  portal.portal_catalog.searchAndActivate(
    method_id='Base_deleteProcessedDocumentDuringPurge',
    portal_type=["Software Product", "Software Release"],
    **packet_kw
  )

############################################
# Gather compute node informations
############################################
portal.portal_catalog.searchAndActivate(
  method_id='ComputeNode_fixupSiteMigrationToVirtualMaster',
  activate_kw={'tag': tag, 'priority': 1},

  portal_type="Compute Node",

  **migrated_select_dict
)

############################################
# Gather instance tree informations
############################################
portal.portal_catalog.searchAndActivate(
  method_id='InstanceTree_fixupSiteMigrationToVirtualMaster',
  method_kw={'tag': tag},
  activate_kw={'tag': tag, 'priority': 1},

  portal_type="Instance Tree",

  **migrated_select_dict
)

if (run_count < 20):
  context.activate(after_tag=tag, priority=4).Base_triggerFullSiteMigrationToVirtualMasterStep2(run_count=run_count+1)

else:
  context.activate(after_tag=tag, priority=4).Base_triggerFullSiteMigrationToVirtualMasterStep4()
