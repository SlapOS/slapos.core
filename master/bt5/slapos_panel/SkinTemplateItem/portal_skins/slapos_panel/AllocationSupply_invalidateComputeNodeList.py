from Products.ERP5Type.Message import translateString
from Products.ZSQLCatalog.SQLCatalog import SimpleQuery, NegatedQuery

allocation_supply = context
portal = context.getPortalObject()
project = allocation_supply.getDestinationProjectValue()


allocation_supply.invalidate()

# Create all missing lines when invalidated
# to reduce the number of user click
already_handled_software_product_uid_list = [x.getResourceUid() for x in allocation_supply.contentValues()] or [-1]
software_product_list = portal.portal_catalog(
  portal_type="Software Product",
  validation_state=['validated', 'published'],
  follow_up__uid=project.getUid(),
  uid=NegatedQuery(SimpleQuery(uid=already_handled_software_product_uid_list))
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

if not batch:
  return allocation_supply.Base_redirect(
    keep_items={'portal_status_message': translateString('Allocation Supply invalidated.')}
  )
