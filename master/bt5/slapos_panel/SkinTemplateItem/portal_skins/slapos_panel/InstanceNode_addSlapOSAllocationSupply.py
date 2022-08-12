from Products.ERP5Type.Message import translateString

portal = context.getPortalObject()
instance_node = context
project = instance_node.getFollowUpValue(portal_type="Project")

allocation_supply = portal.allocation_supply_module.newContent(
  title="%s %s" % (instance_node.getTitle(), DateTime()),
  portal_type="Allocation Supply",
  destination_project_value=project,
  start_date_range_min=DateTime(),
  aggregate_value=instance_node
)

software_product_list = portal.portal_catalog(
  portal_type="Software Product",
  validation_state=['validated', 'published'],
  follow_up__uid=project.getUid(),
)
for sql_software_product in software_product_list:
  allocation_supply_line = allocation_supply.newContent(
    portal_type="Allocation Supply Line",
    title=sql_software_product.getTitle(),
    resource_value=sql_software_product.getObject()
  )
  allocation_supply_line.edit(
    p_variation_base_category_list=allocation_supply_line.getVariationRangeBaseCategoryList()
  )

return allocation_supply.Base_redirect(
  keep_items={'portal_status_message': translateString('New Allocation Supply created.')}
)
