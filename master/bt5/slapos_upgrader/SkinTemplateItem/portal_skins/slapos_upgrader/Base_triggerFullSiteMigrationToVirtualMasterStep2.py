portal = context.getPortalObject()

tag = script.id
not_migrated_select_dict={'default_follow_up_uid': None}

if run_count == 1:
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
    portal_type=["Upgrade Decision"],
    **packet_kw
  )
  portal.portal_catalog.searchAndActivate(
    method_id='Base_deleteProcessedDocumentDuringPurge',
    portal_type=["Regularisation Request"],
    **packet_kw
  )

  ############################################
  # Migrate existing projects
  ############################################
  portal.project_module.activate(**{'tag': tag, 'priority': 1}).ProjectModule_triggerObjectMigrationToVirtualMaster()

############################################
# Gather compute node informations
############################################
portal.portal_catalog.searchAndActivate(
  method_id='ComputeNode_checkSiteMigrationToVirtualMaster',
  method_kw={'force_migration': run_count==5},
  activate_kw={'tag': tag, 'priority': 1},

  portal_type="Compute Node",

  select_dict=not_migrated_select_dict,
  left_join_list=not_migrated_select_dict.keys(),
  **not_migrated_select_dict
)

############################################
# Gather instance tree informations
############################################
portal.portal_catalog.searchAndActivate(
  method_id='InstanceTree_checkSiteMigrationToVirtualMaster',
  activate_kw={'tag': tag, 'priority': 1},

  portal_type="Instance Tree",

  select_dict=not_migrated_select_dict,
  left_join_list=not_migrated_select_dict.keys(),
  **not_migrated_select_dict
)

############################################
# Gather computer network informations
############################################
portal.portal_catalog.searchAndActivate(
  method_id='ComputerNetwork_checkSiteMigrationToVirtualMaster',
  activate_kw={'tag': tag, 'priority': 1},

  portal_type="Computer Network",

  select_dict=not_migrated_select_dict,
  left_join_list=not_migrated_select_dict.keys(),
  **not_migrated_select_dict
)


if run_count < 10:
  # Run the migration script multiple times
  # Because some object are migrated only after some others are migrated
  context.activate(after_tag=tag, priority=4).Base_triggerFullSiteMigrationToVirtualMasterStep2(run_count=run_count+1)
else:
  context.activate(after_tag=tag, priority=4).Base_triggerFullSiteMigrationToVirtualMasterStep3(run_count=run_count)
