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

context.activate(after_tag=tag, priority=4).getId()
