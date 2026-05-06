from Products.ERP5Type.Message import translateString

portal = context.getPortalObject()
project = context

service_list = portal.portal_catalog(
  portal_type="Service",
  validation_state=['validated', 'published'],
  product_line__uid=portal.portal_categories.product_line.cloud.usage.getUid(),
)

if not len(service_list):
  return context.Base_redirect(
    keep_items={'portal_status_message': translateString('No Service found for Consumption use.')}
)

consumption_supply = portal.consumption_supply_module.newContent(
  title="%s %s" % (project.getReference(), DateTime()),
  portal_type="Consumption Supply",
  destination_project_value=project,
  start_date_range_min=DateTime()
)

for sql_service in service_list:
  consumption_supply.newContent(
    portal_type="Consumption Supply Line",
    title=sql_service.getTitle(),
    resource_value=sql_service.getObject()
  )

return consumption_supply.Base_redirect(
  keep_items={'portal_status_message': translateString('New Consumption Supply created.')}
)
