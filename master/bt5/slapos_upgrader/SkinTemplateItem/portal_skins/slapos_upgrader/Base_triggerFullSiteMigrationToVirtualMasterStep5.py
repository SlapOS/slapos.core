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
  method_id='ComputeNode_checkAllocationSupplyToVirtualMaster',

  portal_type="Compute Node",
  allocation_scope__uid=portal.portal_categories.allocation_scope.open.getUid(),
  **packet_kw
)

portal.portal_catalog.searchAndActivate(
  method_id='RemoteNode_checkAllocationSupplyToVirtualMaster',

  portal_type="Remote Node",
  allocation_scope__uid=portal.portal_categories.allocation_scope.open.getUid(),
  **packet_kw
)

portal.portal_catalog.searchAndActivate(
  method_id='InstanceNode_checkAllocationSupplyToVirtualMaster',

  portal_type="Instance Node",
  **packet_kw
)

context.activate(after_tag=tag, priority=4).Base_triggerFullSiteMigrationToVirtualMasterStep6()
