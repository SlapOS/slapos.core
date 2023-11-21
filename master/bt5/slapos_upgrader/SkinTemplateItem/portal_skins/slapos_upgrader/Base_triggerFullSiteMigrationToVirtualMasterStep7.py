portal = context.getPortalObject()

tag = script.id

############################################
# Migrate Support Requests
############################################
packet_kw = {
  'method_kw': {'activate_kw': {'tag': tag}},
  'activate_kw': {'tag': tag, 'priority': 1},
  'packet_size': 1, # Separate calls to many transactions (calculation can take time)
  'activity_count': 1000,
}

portal.portal_catalog.searchAndActivate(
  method_id='SupportRequest_checkSiteMigrationToVirtualMaster',

  portal_type="Support Request",
  **packet_kw
)

# Delete existing old product only
if portal.portal_catalog.getResultValue(portal_type="Software Release") is not None:
  packet_kw = {
    'activate_kw': {'tag': tag, 'priority': 1},
    'packet_size': 1, # Separate calls to many transactions (calculation can take time)
    'activity_count': 1000,
  }
  not_migrated_select_dict={'default_follow_up_uid': None}

  portal.portal_catalog.searchAndActivate(
    method_id='Base_deleteProcessedDocumentDuringPurge',
    portal_type="Software Release",
    **packet_kw
  )
  portal.portal_catalog.searchAndActivate(
    method_id='Base_deleteProcessedDocumentDuringPurge',
    portal_type="Software Product",
    select_dict=not_migrated_select_dict,
    left_join_list=not_migrated_select_dict.keys(),
    default_follow_up_uid=None,
    **packet_kw
  )

context.activate(after_tag=tag, priority=4).getId()
