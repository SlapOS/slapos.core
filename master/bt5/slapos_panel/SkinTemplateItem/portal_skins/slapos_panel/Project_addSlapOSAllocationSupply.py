from Products.ERP5Type.Message import translateString

portal = context.getPortalObject()
project = context

compute_node_list = portal.portal_catalog(
  portal_type="Compute Node",
  validation_state='validated',
  follow_up__uid=project.getUid(),
  allocation_scope__uid=portal.restrictedTraverse("portal_categories/allocation_scope/open").getUid(),
)

allocation_supply = portal.allocation_supply_module.newContent(
  title="All compute nodes %s" % DateTime(),
  portal_type="Allocation Supply",
  destination_project_value=project,
  start_date_range_min=DateTime(),
  aggregate_list=[x.getRelativeUrl() for x in compute_node_list]
)
# immediately invalidate to generate all possible lines
allocation_supply.AllocationSupply_invalidateComputeNodeList(batch=1)

return allocation_supply.Base_redirect(
  keep_items={'portal_status_message': translateString('New Allocation Supply created.')}
)
