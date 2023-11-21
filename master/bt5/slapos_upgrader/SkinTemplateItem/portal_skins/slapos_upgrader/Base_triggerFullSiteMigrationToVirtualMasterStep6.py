# create the software products
################################################
portal = context.getPortalObject()

tag = script.id

############################################
# Create allocation supply
############################################
packet_kw = {
  'method_kw': {'activate_kw': {'tag': tag}},
  'activate_kw': {'tag': tag, 'priority': 1},
  'packet_size': 1, # Separate calls to many transactions (calculation can take time)
  'activity_count': 1000,
}

portal.portal_catalog.searchAndActivate(
  method_id='OpenSaleOrder_checkSubscriptionRequestToVirtualMaster',

  portal_type="Open Sale Order",
  validation_state="validated",
  **packet_kw
)

portal.portal_catalog.searchAndActivate(
  method_id='Person_checkAssignmentToVirtualMaster',

  portal_type="Person",
  **packet_kw
)

context.activate(after_tag=tag, priority=4).Base_triggerFullSiteMigrationToVirtualMasterStep7()
