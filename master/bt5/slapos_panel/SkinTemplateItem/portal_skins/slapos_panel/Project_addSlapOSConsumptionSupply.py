from Products.ERP5Type.Message import translateString

portal = context.getPortalObject()
project = context

compute_node_list = portal.portal_catalog(
  portal_type="Compute Node",
  validation_state=['validated', 'published'],
  follow_up__uid=project.getUid(),
  allocation_scope__uid=portal.restrictedTraverse("portal_categories/allocation_scope/open").getUid(),
)

service_list = portal.portal_catalog(
  portal_type="Service",
  validation_state=['validated', 'published'],
  use__uid=portal.portal_categories.use.trade.consumption.getUid(),
)

if not len(service_list):
  return context.Base_redirect(
    keep_items={'portal_status_message': translateString('No Service found for Consumption use.')}
)

sale_supply_line_list = portal.portal_catalog(
  portal_type="Sale Supply Line",
  parent_portal_type="Sale Trade Condition",
  source_project__uid=project.getUid(),
  resource__uid=[sql_service.uid for sql_service in service_list],
  validation_state='validated',
  group_by=('resource__uid',)
)

if not len(sale_supply_line_list):
  return context.Base_redirect(
    keep_items={'portal_status_message': translateString('No Service found on Sale Trade Conditions to use.')}
)

consumption_supply = portal.consumption_supply_module.newContent(
  title="All compute nodes %s" % DateTime(),
  portal_type="Consumption Supply",
  destination_project_value=project,
  start_date_range_min=DateTime(),
  aggregate_list=[x.getRelativeUrl() for x in compute_node_list]
)

for sql_sale_supply_line in sale_supply_line_list:
  consumption_supply.newContent(
    portal_type="Consumption Supply Line",
    title=sql_service.getTitle(),
    resource_value=sql_sale_supply_line.getResourceValue()
  )

return consumption_supply.Base_redirect(
  keep_items={'portal_status_message': translateString('New Consumption Supply created.')}
)
