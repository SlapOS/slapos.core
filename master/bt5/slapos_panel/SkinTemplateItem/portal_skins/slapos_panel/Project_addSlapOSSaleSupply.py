from Products.ERP5Type.Message import translateString

portal = context.getPortalObject()
project = context

sql_result_list = portal.portal_catalog(
  portal_type="Sale Trade Condition",
  source_project__uid=project.getUid(),
  validation_state="validated",
  group_by_list=["price_currency_uid"]
)
price_currency = None
if len(sql_result_list) == 1:
  price_currency = sql_result_list[0].getPriceCurrencyValue()

sale_supply = portal.sale_supply_module.newContent(
  title="All %s" % DateTime(),
  portal_type="Sale Supply",
  source_project_value=project,
  price_currency_value=price_currency,
  start_date_range_min=DateTime()
)

software_product_list = portal.portal_catalog(
  portal_type="Software Product",
  validation_state=['validated', 'published'],
  follow_up__uid=project.getUid(),
)
for sql_software_product in software_product_list:
  sale_supply.newContent(
    portal_type="Sale Supply Line",
    title=sql_software_product.getTitle(),
    resource_value=sql_software_product.getObject()
  )

compute_node_service = portal.restrictedTraverse('service_module/slapos_compute_node_subscription')
sale_supply.newContent(
  portal_type="Sale Supply Line",
  title=compute_node_service.getTitle(),
  resource_value=compute_node_service
)

return sale_supply.Base_redirect(
  keep_items={'portal_status_message': translateString('New Sale Supply created.')}
)
